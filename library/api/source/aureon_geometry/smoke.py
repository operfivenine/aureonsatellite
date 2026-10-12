"""Explicit developer self-test, always uses a separate INI/media profile."""
from pathlib import Path
import os,time,json,math,wave,faulthandler
import sys

def main(output,package):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    trace=(output/'selftest_trace.log').open('w')
    faulthandler.dump_traceback_later(20,repeat=True,file=trace)
    def probe(value):
        with (output/'selftest_steps.log').open('a',encoding='utf-8') as steps:steps.write(f'{time.perf_counter():.3f} {value}\n')
        return value
    os.environ['AUREON_DATA_ROOT']=str(output/'profile')
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt,QSettings,QCoreApplication,QEvent,QEventLoop
    import aureon_paths
    profile=output/'profile';profile.mkdir(exist_ok=True)
    aureon_paths.settings_args=lambda:(str(profile/'settings.ini'),QSettings.IniFormat)
    import numpy as np
    tone=output/'tone.wav'
    t=np.arange(16000*20,dtype=np.float32)/16000
    data=(4000*(np.sin(t*math.tau*90)+.3*np.sin(t*math.tau*800)+.3*np.sin(t*math.tau*5000))*(.4+.6*np.sin(t*9)**2)).astype('<i2')
    with wave.open(str(tone),'wb') as f:f.setparams((1,2,16000,0,'NONE','not compressed'));f.writeframes(data.tobytes())
    s=QSettings(*aureon_paths.settings_args());s.clear();s.setValue('queue/paths',[str(tone)]);s.setValue('queue/current_path',str(tone))
    s.setValue('visual/idle_style','default');s.setValue('visual/idle_reactive',True)
    from media.session import PlaybackSessionStore
    PlaybackSessionStore(s).save(str(tone),3000)
    app=QApplication([]);app.setStyle('Fusion')
    from player import PlayerWindow
    w=PlayerWindow();w.setAttribute(Qt.WA_DontShowOnScreen,True);w.audio.setVolume(0);w.show()
    def wait(predicate,timeout=12):
        end=time.perf_counter()+timeout
        while time.perf_counter()<end:
            app.processEvents(QEventLoop.AllEvents,5)
            if predicate():return True
            time.sleep(.003)
        return bool(predicate())
    report={'success':False};step=probe('queue restore')
    try:
        assert wait(lambda:w.current_path==str(tone) and w.player.duration()>0),'Queue did not restore'
        step=probe('mesh import')
        entry=w.scene_package_store.install(package);w.apply_idle_visual(entry.id)
        assert wait(lambda:w.surface._gl_widget and w.surface._gl_widget.ready),str(w.surface._gl_failure)
        step=probe('playback')
        native=w.player;native.play();assert wait(lambda:native.playbackState().name=='PlayingState'),'Playback did not start'
        step=probe('audio bridge')
        assert wait(lambda:w.surface._gl_widget._runtime.bridge.peak_input['low']>0),'Analyzer did not supply low band'
        step=probe('quality switching')
        counts=[]
        for q in ('low','medium','high'):
            w.apply_visual_quality(q);assert wait(lambda:w.surface._gl_widget and w.surface._gl_widget.ready)
            counts.append(w.surface._gl_widget.scene.vertex_count)
        assert counts[0]<counts[1]<counts[2]
        gl=w.surface._gl_widget;wait(lambda:False,.2);before=gl._runtime.seconds;native.pause();wait(lambda:False,.4)
        assert gl._runtime.seconds>before+.25
        step=probe('hybrid shared state')
        shader=gl._runtime.shader_controller
        assert shader is not None and gl.hybrid_program is not None
        assert gl.textures.stats['count']==6
        assert shader.signals['bass']>=0
        assert (any(a['type']=='path' for _,a,_ in gl.scene.animations) or
                any(n.get('animation',{}).get('type')=='path' for n in (gl._runtime.definition.document.get('object_graph') or {}).get('nodes',[])))
        assert shader.values['u_time']==gl._runtime.seconds
        for band in ('low','mid','high'):
            assert shader.values['u_audio_'+band]==getattr(gl._runtime.response,band)
        assert gl.scene.graph is not None
        assert gl.instancing is not None
        gl._runtime.set_camera_preset('approach')
        gl.grabFramebuffer()
        object_metrics=gl.performance_snapshot()['geometry']['objects']
        reflection_metrics=gl.performance_snapshot()['geometry'].get('reflections',{})
        aa=gl.performance_snapshot()['antialiasing_details']
        assert aa['msaa_samples']>=2 and aa['msaa_active']
        assert aa['scene']['enabled'] and aa['reflection']['enabled']
        assert reflection_metrics.get('passes',0)>0 and not reflection_metrics.get('reason')
        assert object_metrics['visible']>0 and object_metrics['instance_draw_calls']>0
        gl.grabFramebuffer().save(str(output/'frozen_frame.png'))
        alpha=sum(getattr(mesh['item'],'blend_mode','')=='alpha' for mesh in gl.meshes)
        loop_errors=None
        if alpha:
            first,target=gl.scene.camera_pose(0);last,end_target=gl.scene.camera_pose(gl.scene.loop_seconds)
            loop_errors=(float(np.linalg.norm(first-last)),float(np.linalg.norm(target-end_target)))
            assert max(loop_errors)<1e-9
        probe('geometry fullscreen and AA resize')
        w.toggle_fullscreen();assert w.isFullScreen();wait(lambda:False,.25)
        w.surface._gl_widget.grabFramebuffer()
        w.toggle_fullscreen();assert not w.isFullScreen();wait(lambda:False,.25)
        live=w.surface._gl_widget;live.grabFramebuffer()
        assert live.ready and live.performance_snapshot()['antialiasing_details']['scene']['enabled']
        probe('stable theme');w.apply_idle_visual('orbital_dawn_gl');assert wait(lambda:w.surface._gl_widget and w.surface._gl_widget.ready)
        w.toggle_fullscreen();assert w.isFullScreen();wait(lambda:False,.2);w.toggle_fullscreen();assert not w.isFullScreen()
        assert w.player is native
        report=dict(success=True,frozen=bool(getattr(sys,'frozen',False)),geometry_import=True,quality_vertices=counts,audio_real=True,pause_clock=True,stable_renderer_after=True,fullscreen=True,
                    hybrid=True,shared_clock=True,shared_audio=True,shared_depth=True,
                    materials=True,textures=6,shared_signals=True,curved_paths=True,
                    mesh_objects=object_metrics,reflections=reflection_metrics,private_ini=w.settings.fileName(),device=gl.device_info)
        report['alpha_batches']=alpha
        report['antialiasing']=aa
        report['geometry_fullscreen']=True
        from aureon_gpu_preferences import snapshot
        report['gpu_preferences']=snapshot()
        if loop_errors:
            report['camera_loop_position_error'],report['camera_loop_target_error']=loop_errors
    except Exception as exc:
        import traceback
        report.update(error=str(exc),step=step,trace=traceback.format_exc())
    finally:
        probe('closing player')
        w._tray_force_quit=True;w.close();QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents()
        (output/'frozen_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        probe('finished');faulthandler.cancel_dump_traceback_later();trace.close()
    return 0 if report['success'] else 1
