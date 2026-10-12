"""Stateful AURS v2 controller: 60 Hz behavior, 30 Hz reactive analysis.

The runtime owns all temporal state.  Packages provide only validated numeric
expressions/descriptors; no package code is executed.
"""
from collections import deque
from dataclasses import dataclass
import math
import random
import time

from .scene_audio import SceneAudioContext
from .shader_library import library_source


@dataclass(frozen=True)
class UniformArray:
    values: tuple


def _clamp(value, low=0.0, high=1.0):
    try:
        value=float(value)
    except (TypeError,ValueError):
        return low
    if not math.isfinite(value): return low
    return max(low,min(high,value))


def _approach(current,target,tau,dt):
    return current+(target-current)*(1.-math.exp(-dt/max(.001,tau)))


class PackageSceneRuntimeV2:
    def __init__(self,definition,quality,reactive):
        self.definition=definition
        self.quality=quality if quality in definition.quality else ('high' if quality == 'extreme' else 'medium')
        self.reactive=bool(reactive)
        self.scene=self
        self.elapsed=0.0
        self.values={}
        self.zones=(0.0,)*8
        self.audio_context=SceneAudioContext()
        # OPT 03: the expression context only contains stable object references
        # plus time/dt. Reuse it instead of allocating two dictionaries per tick.
        self._eval_context={'time':0.0,'dt':1./60.,'pi':math.pi,
                            'audio':self.audio_context.audio,'runtime':self.audio_context.runtime,
                            'signal':{}}
        self.accumulator=0.
        self.mode=0; self.mode_age=0.; self.energy=0.
        self.weights=[1.,0.,0.,0.]
        self.random=random.Random(definition.behavior['seed'])
        self.variant=self.random.random()

        self.signals={spec.name:float(spec.params.get('initial',0.0)) for spec in definition.signals}
        self._eval_context['signal']=self.signals
        self.signal_state={}
        for spec in definition.signals:
            state={}
            if spec.kind=='derivative': state['previous']=None
            elif spec.kind=='spring': state['velocity']=0.0
            elif spec.kind=='gate': state['latched']=self.signals[spec.name]>=.5
            elif spec.kind=='history':
                state['values']=deque(); state['events']=deque(); state['previous']=0.0
                state['last_event']=-1e9
            self.signal_state[spec.name]=state

        self.event_specs=definition.behavior['events']
        self.events=[]
        self.event_groups=[]
        self.cooldowns=[0.]*len(self.event_specs)
        self.previous=[0.]*len(self.event_specs)
        for group,spec in enumerate(self.event_specs):
            slots=[dict(age=spec['duration'],duration=spec['duration'],strength=0.,seed=0.,group=group)
                   for _ in range(spec['slots'])]
            self.event_groups.append(slots)
            self.events.extend(slots)

        self.camera=definition.behavior.get('camera')
        self.camera_preset='auto'
        self._manual_origin=None
        self._manual_goal=None
        self._manual_offsets=(0.,0.,1.)
        self.camera_shot=0; self.camera_shot_age=0.; self.camera_transition_age=99.; self.camera_hold_age=0.
        self._camera_from=None
        self._camera_current=((0.,0.,5.),(0.,0.,0.),45.,0.)
        if self.camera:
            self.camera_shot=(self.camera['mode_shots'][0] if self.camera['driver']=='mode' else 0)
            self._camera_current=self._eval_camera_shot(self.camera_shot,self._context(1./60.))

        lines=definition.source.splitlines(keepends=True)
        insertion=next(i for i,line in enumerate(lines) if line.lstrip().startswith('#version'))+1
        quality_index={'low':0,'medium':1,'high':2,'extreme':3}[self.quality]
        defines=f'#define AUR_QUALITY_TIER {quality_index}\n#define AUR_QUALITY_LEVEL {float(quality_index):.1f}\n'+''.join(f'#define {name} {value}\n' for name,value in definition.quality[self.quality].items())
        helpers=library_source(definition.libraries)
        lines.insert(insertion,'\n'+defines+helpers)
        self.shader_source=''.join(lines)
        self._publish()

    def _context(self,dt):
        context=self._eval_context
        context['time']=self.elapsed
        context['dt']=dt
        return context

    def _signal(self,spec,context,dt):
        name=spec.name; p=spec.params; current=self.signals[name]
        raw=spec.expr.value(context)
        state=self.signal_state[name]
        if spec.kind=='expression':
            return raw
        if spec.kind=='integrator':
            return (current+raw*dt)%p['wrap']
        if spec.kind=='envelope':
            return _approach(current,raw,p['attack'] if raw>current else p['release'],dt)
        if spec.kind=='derivative':
            previous=state['previous']; state['previous']=raw
            target=0. if previous is None else (raw-previous)/max(1e-6,dt)*p['scale']
            if p['absolute']: target=abs(target)
            return _clamp(_approach(current,target,p['attack'] if target>current else p['release'],dt),-1000000.,1000000.)
        if spec.kind=='spring':
            omega=math.tau*p['frequency']
            velocity=state['velocity']
            acceleration=(raw-current)*omega*omega-2.*p['damping']*omega*velocity
            velocity+=acceleration*dt
            value=current+velocity*dt
            if value<=p['min'] and velocity<0.: velocity=0.
            if value>=p['max'] and velocity>0.: velocity=0.
            state['velocity']=velocity
            return _clamp(value,p['min'],p['max'])
        if spec.kind=='gate':
            latched=state['latched']
            if not latched and raw>=p['on']: latched=True
            elif latched and raw<=p['off']: latched=False
            state['latched']=latched
            target=1. if latched else 0.
            return _approach(current,target,p['attack'] if target>current else p['release'],dt)
        if spec.kind=='state':
            value=current*math.exp(-p['damping']*dt)+raw*dt
            if p['wrap']>0.: value%=p['wrap']
            else: value=_clamp(value,p['min'],p['max'])
            return value
        if spec.kind=='history':
            cutoff=self.elapsed-p['window']
            if p['mode'] not in ('interval','rate'):
                values=state['values']; values.append((self.elapsed,raw))
                while values and values[0][0]<cutoff: values.popleft()
                if not values: return p['initial']
                mode=p['mode']
                iterator=iter(values)
                _,first=next(iterator)
                if mode=='mean':
                    total=first; count=1
                    for _,value in iterator:
                        total+=value; count+=1
                    return total/count
                result=first
                if mode=='max':
                    for _,value in iterator:
                        if value>result: result=value
                else:
                    for _,value in iterator:
                        if value<result: result=value
                return result
            events=state['events']; previous=state['previous']; rise=raw-previous
            state['previous']=raw
            crossed=raw>=p['threshold'] and previous<p['threshold'] and rise>=p['rise']
            if crossed and self.elapsed-state['last_event']>=p['min_interval']:
                events.append(self.elapsed); state['last_event']=self.elapsed
            while events and events[0]<cutoff: events.popleft()
            if len(events)<p['min_events'] or self.elapsed-events[-1]>p['stale']: return 0.0
            interval=(events[-1]-events[0])/max(1,len(events)-1)
            if p['mode']=='interval': return interval
            freshness=max(0.0,1.0-(self.elapsed-events[-1])/p['stale'])
            return (1.0/max(p['min_interval'],interval))*freshness
        return raw

    def _signals(self,dt):
        context=self._context(dt)
        for spec in self.definition.signals:
            self.signals[spec.name]=self._signal(spec,context,dt)

    def _modes(self,audio,active,dt,context):
        c=self.definition.behavior['modes']
        if c.get('source') is not None:
            target=_clamp(c['source'].value(context)) if active else 0.
        else:
            target=max(audio['energy'],audio['low']*.8,audio['fast']*.65) if active else 0.
        self.energy+=(target-self.energy)*(1.-math.exp(-dt/(.45 if target>self.energy else .9)))
        self.mode_age+=dt
        destination=self.mode
        if not active:
            destination=3 if self.mode in (1,2) else (0 if self.mode==3 and self.mode_age>=c['recover'] else self.mode)
        elif self.mode==0 and self.mode_age>=c['dwell'] and self.energy>=c['active_on']: destination=1
        elif self.mode==1 and self.mode_age>=c['dwell']:
            if self.energy>=c['peak_on']: destination=2
            elif self.energy<=c['active_off']: destination=3
        elif self.mode==2 and self.mode_age>=c['peak_hold'] and self.energy<=c['peak_off']: destination=3
        elif self.mode==3 and self.mode_age>=c['recover']: destination=1 if self.energy>=c['active_on'] else 0
        if destination!=self.mode:
            self.mode=destination; self.mode_age=0.
        blend=1.-math.exp(-dt/c['blend'])
        for i in range(4): self.weights[i]+=((1. if self.mode==i else 0.)-self.weights[i])*blend

    def _events(self,audio,active,dt,context):
        for event in self.events: event['age']=min(event['duration'],event['age']+dt)
        for group,spec in enumerate(self.event_specs):
            value=spec['source'].value(context) if spec['source'] is not None else audio[spec['channel']]
            if not math.isfinite(value): value=0.
            rise=value-self.previous[group]
            self.previous[group]=value
            self.cooldowns[group]=max(0.,self.cooldowns[group]-dt)
            if not active or self.cooldowns[group]>0.: continue
            if spec['edge']=='rise': trigger=value>=spec['threshold'] and rise>=spec['rise']
            elif spec['edge']=='fall': trigger=value<=spec['threshold'] and -rise>=spec['rise']
            else: trigger=value>=spec['threshold']
            if not trigger: continue
            event=None
            for candidate in self.event_groups[group]:
                if candidate['age']>=candidate['duration']:
                    event=candidate
                    break
            if event is None: continue
            strength=(spec['strength'].value(context) if spec['strength'] is not None
                      else .25+abs(value)*.6+abs(rise)*2.)
            event.update(age=0.,strength=_clamp(strength),seed=self.random.random())
            self.cooldowns[group]=spec['cooldown']

    def _eval_camera_shot(self,index,context):
        if not self.camera:
            return ((0.,0.,5.),(0.,0.,0.),45.,0.)
        shot=self.camera['shots'][index]
        limits=self.camera['limits']
        pos=[]; target=[]
        for axis,e in enumerate(shot.position):
            lo,hi=limits['position'][axis]
            pos.append(_clamp(e.value(context),lo,hi))
        for axis,e in enumerate(shot.target):
            lo,hi=limits['target'][axis]
            target.append(_clamp(e.value(context),lo,hi))
        pos=tuple(pos); target=tuple(target)

        # Optional distance gives authors a true dolly control while retaining
        # the shot's XYZ direction.  All cameras, including direct XYZ shots,
        # are finally constrained by the declared distance range.
        dx=pos[0]-target[0]; dy=pos[1]-target[1]; dz=pos[2]-target[2]
        length=math.sqrt(dx*dx+dy*dy+dz*dz)
        if length<1e-6:
            dx,dy,dz,length=0.,0.,1.,1.
        ux,uy,uz=dx/length,dy/length,dz/length
        requested=(shot.distance.value(context) if shot.distance is not None else length)
        dlo,dhi=limits['distance']
        # Intersect the dolly range with the XYZ box along this viewing ray, so
        # both classes of camera limits remain hard bounds when compatible.
        feasible_lo,feasible_hi=dlo,dhi
        for i,u in enumerate((ux,uy,uz)):
            lo,hi=limits['position'][i]; origin=target[i]
            if abs(u)<1e-9:
                if not lo<=origin<=hi:
                    feasible_lo,feasible_hi=1.,0.
                    break
                continue
            a=(lo-origin)/u; b=(hi-origin)/u
            if a>b: a,b=b,a
            feasible_lo=max(feasible_lo,a); feasible_hi=min(feasible_hi,b)
        if feasible_lo<=feasible_hi:
            distance=_clamp(requested,feasible_lo,feasible_hi)
            pos=(target[0]+ux*distance,target[1]+uy*distance,target[2]+uz*distance)
        else:
            # Contradictory author limits cannot be satisfied simultaneously;
            # preserve the XYZ safety box rather than emitting an unsafe value.
            distance=_clamp(requested,dlo,dhi); scale=distance/length
            projected=(target[0]+dx*scale,target[1]+dy*scale,target[2]+dz*scale)
            pos=tuple(_clamp(projected[i],*limits['position'][i]) for i in range(3))

        fov=_clamp(shot.fov.value(context),*limits['fov'])
        roll=_clamp(shot.roll.value(context),-math.pi,math.pi)
        return pos,target,fov,roll

    def _camera_ease(self,t):
        t=_clamp(t)
        mode=self.camera['easing'] if self.camera else 'smoothstep'
        if mode=='linear': return t
        if mode=='smootherstep': return t*t*t*(t*(t*6.-15.)+10.)
        if mode=='sine': return .5-.5*math.cos(math.pi*t)
        return t*t*(3.-2.*t)

    def _mix_camera(self,a,b,t):
        t=self._camera_ease(t)
        vec=lambda x,y: tuple(i+(j-i)*t for i,j in zip(x,y))
        return vec(a[0],b[0]),vec(a[1],b[1]),a[2]+(b[2]-a[2])*t,a[3]+(b[3]-a[3])*t

    def _begin_camera_transition(self,desired):
        if desired==self.camera_shot: return
        self._camera_from=self._camera_current
        self.camera_shot=desired
        self.camera_shot_age=0.
        self.camera_transition_age=0.
        self.camera_hold_age=0.

    def begin_manual_camera(self):
        if not self.camera or not self.camera.get('presets'):return False
        if self.camera_preset=='manual':return True
        manual=self.camera.get('manual')
        if manual:
            pos,target,_,_=self._camera_current
            az,el,radius=self._orbit_coordinates(pos,target)
            values=(math.degrees(az),math.degrees(el),radius)
            if any(not manual[key][0]-1e-5<=value<=manual[key][1]+1e-5 for key,value in zip(('yaw','pitch','distance'),values)):
                return False
        self._manual_origin=self._camera_current
        self._manual_goal=self._camera_current
        self._manual_offsets=(0.,0.,1.)
        self._camera_from=None
        self.camera_preset='manual'
        return True

    @staticmethod
    def _orbit_coordinates(pos,target):
        x,y,z=(pos[i]-target[i] for i in range(3))
        radius=max(1e-6,math.sqrt(x*x+y*y+z*z))
        return math.atan2(x,z),math.asin(_clamp(y/radius,-1.,1.)),radius

    def manual_control_ranges(self):
        manual=self.camera.get('manual') if self.camera else None
        if not manual or self._manual_origin is None:return ((-15.,15.),(-10.,10.),(.8,1.2))
        pos,target,_,_=self._manual_origin
        az,el,radius=self._orbit_coordinates(pos,target)
        return (tuple(v-math.degrees(az) for v in manual['yaw']),
                tuple(v-math.degrees(el) for v in manual['pitch']),
                tuple(v/radius for v in manual['distance']))

    def adjust_manual_camera(self,yaw,pitch,scale):
        if self.camera_preset!='manual' or self._manual_origin is None:return False
        ranges=self.manual_control_ranges()
        yaw=_clamp(yaw,*ranges[0]);pitch=_clamp(pitch,*ranges[1]);scale=_clamp(scale,*ranges[2])
        pos,target,fov,roll=self._manual_origin
        d=tuple(pos[i]-target[i] for i in range(3))
        length=math.sqrt(sum(v*v for v in d))
        if length<1e-6:return False
        az=math.atan2(d[0],d[2])+math.radians(yaw)
        el=_clamp(math.asin(_clamp(d[1]/length,-1.,1.))+math.radians(pitch),-1.48,1.48)
        direction=(math.sin(az)*math.cos(el),math.sin(el),math.cos(az)*math.cos(el))
        manual=self.camera.get('manual')
        if manual:
            distance=_clamp(length*scale,*manual['distance'])
            self._manual_goal=(tuple(target[i]+direction[i]*distance for i in range(3)),target,fov,roll)
            self._manual_offsets=(yaw,pitch,distance/length)
            return True
        lo,hi=self.camera['limits']['distance']
        for i,u in enumerate(direction):
            a,b=self.camera['limits']['position'][i]
            if abs(u)<1e-9:
                if not a<=target[i]<=b:return False
            else:
                a=(a-target[i])/u;b=(b-target[i])/u
                lo=max(lo,min(a,b));hi=min(hi,max(a,b))
        if lo>hi:return False
        distance=_clamp(length*scale,lo,hi)
        self._manual_goal=(tuple(target[i]+direction[i]*distance for i in range(3)),target,fov,roll)
        self._manual_offsets=(yaw,pitch,scale)
        return True

    def reset_manual_camera(self):
        if self.camera_preset!='manual':return
        self._manual_goal=self._manual_origin
        self._manual_offsets=(0.,0.,1.)

    def set_camera_preset(self,ident):
        if not self.camera:return False
        presets={p[0]:p[3] for p in self.camera.get('presets',())}
        if ident!='auto' and ident not in presets:return False
        if ident==self.camera_preset:return True
        was_manual=self.camera_preset=='manual'
        self.camera_preset=ident
        self.camera_hold_age=0.
        if was_manual:
            self._camera_from=self._camera_current
            self.camera_transition_age=0.
            self._manual_goal=None
        if ident!='auto':self._begin_camera_transition(presets[ident])
        elif self.camera['driver']=='static':self._begin_camera_transition(0)
        # Auto resumes the authored driver from the current pose/shot.
        # Timeline holds before advancing; mode transitions on the next step.
        return True

    def _camera_step(self,dt):
        if not self.camera: return
        self.camera_shot_age+=dt
        self.camera_transition_age+=dt
        if self.camera_preset=='manual':
            if self._manual_goal is not None:
                a=self._camera_current;b=self._manual_goal
                k=1.-math.exp(-dt/.10)
                if self.camera.get('manual'):
                    # Interpolate orbit coordinates, not a chord through the object.
                    az,el,radius=self._orbit_coordinates(a[0],b[1])
                    baz,bel,br=self._orbit_coordinates(b[0],b[1])
                    az+=(baz-az)*k;el+=(bel-el)*k;radius+=(br-radius)*k
                    direction=(math.sin(az)*math.cos(el),math.sin(el),math.cos(az)*math.cos(el))
                    pos=tuple(b[1][i]+direction[i]*radius for i in range(3))
                else:
                    pos=tuple(i+(j-i)*k for i,j in zip(a[0],b[0]))
                self._camera_current=(pos,b[1],b[2],b[3])
            return
        if self.camera_preset!='auto':return
        driver=self.camera['driver']
        if driver=='mode':
            self._begin_camera_transition(self.camera['mode_shots'][self.mode])
            return
        if driver=='static':
            return

        # Timeline driver is deliberately independent of music.  It holds each
        # authored shot, then moves to the next one using a bounded transition.
        # Hold time starts after arrival so the viewer can actually read a shot.
        if self.camera_transition_age < self.camera['transition']:
            return
        self.camera_hold_age+=dt
        hold=self.camera['shots'][self.camera_shot].hold
        if self.camera_hold_age < hold:
            return
        desired=self.camera_shot+1
        if desired>=len(self.camera['shots']):
            if not self.camera['loop']:
                self.camera_hold_age=hold
                return
            desired=0
        self._begin_camera_transition(desired)

    def _camera_values(self,context):
        if not self.camera:
            return ((0.,0.,5.),(0.,0.,0.),45.,0.),(0.,0.,0.,0.)
        if self.camera_preset=='manual':return self._camera_current,(0.,0.,0.,0.)
        target=self._eval_camera_shot(self.camera_shot,context)
        if self._camera_from is not None and self.camera_transition_age<self.camera['transition']:
            current=self._mix_camera(self._camera_from,target,self.camera_transition_age/self.camera['transition'])
        else:
            current=target; self._camera_from=None
        self._camera_current=current

        # Event impulses remain only for legacy mode-driven packages.  New
        # static/timeline camera rigs never inherit audio/event camera motion.
        x=y=roll=zoom=0.
        if self.camera['driver']=='mode':
            for rule in self.camera['impulses']:
                for event in self.events:
                    if event['group']!=rule['group'] or event['age']>=event['duration']: continue
                    amplitude=event['strength']*math.exp(-event['age']/rule['decay'])
                    phase=event['seed']*37.731+event['age']*31.0
                    x+=math.sin(phase)*rule['shake']*amplitude
                    y+=math.cos(phase*1.173)*rule['shake']*amplitude
                    roll+=math.sin(phase*.733)*rule['roll']*amplitude
                    zoom+=rule['zoom']*amplitude
        return current,(x,y,roll,zoom)

    def _step(self,frame):
        dt=1./60.
        self.elapsed+=dt
        self.audio_context.step(frame,self.reactive)
        audio=self.audio_context.audio
        active=self.audio_context.playing
        self._signals(dt)
        context=self._context(dt)
        self._modes(audio,active,dt,context)
        self._events(audio,active,dt,context)
        self._camera_step(dt)

    def _publish(self):
        audio=self.audio_context.audio
        context=self._context(1./60.)
        self.values={'u_time':self.elapsed, **{'u_audio_'+k:v for k,v in audio.items()}}
        for name,(kind,expressions) in self.definition.uniforms.items():
            values=tuple(e.value(context) for e in expressions)
            self.values[name]=values[0] if kind=='float' else values
        packed=[(e['age']/e['duration'] if e['age']<e['duration'] else -1.,e['strength'],e['seed'],float(e['group'])) for e in self.events]
        event_array_size = getattr(self.definition, 'event_array_size', 8)
        packed = packed[:event_array_size]
        packed.extend([(-1.,0.,0.,0.)]*(event_array_size-len(packed)))
        camera,impulse=self._camera_values(context)
        self.values.update(
            u_modes=tuple(self.weights),u_mode=float(self.mode),u_mode_age=self.mode_age,
            u_variant=self.variant,u_playing=float(self.audio_context.playing),
            u_bands=UniformArray(tuple(self.audio_context.bands)),u_peaks=UniformArray(tuple(self.audio_context.peaks)),
            u_events=UniformArray(tuple(packed)),
            u_camera_pos=tuple(camera[0]),u_camera_target=tuple(camera[1]),u_camera_fov=camera[2],
            u_camera_roll=camera[3],
            u_camera_distance=math.sqrt(sum((camera[0][i]-camera[1][i])**2 for i in range(3))),
            u_camera_shot=float(self.camera_shot),u_camera_shot_age=self.camera_shot_age,
            u_camera_impulse=tuple(impulse),
        )
        self.zones=self.audio_context.zones

    def update(self,dt,frame):
        if not math.isfinite(dt): return
        started=time.perf_counter_ns()
        self.accumulator+=max(0.,min(.25,dt))
        while self.accumulator+1e-9>=1./60.:
            self._step(frame)
            self.accumulator-=1./60.
        behavior_done=time.perf_counter_ns()
        self._publish()
        publish_done=time.perf_counter_ns()
        self._perf_behavior_ms=(behavior_done-started)/1_000_000.0
        self._perf_uniform_prep_ms=(publish_done-behavior_done)/1_000_000.0

    def performance_timings(self):
        return {
            'cpu_behavior': getattr(self,'_perf_behavior_ms',None),
            'uniform_prep': getattr(self,'_perf_uniform_prep_ms',None),
        }

    def uniforms(self):
        return self.values,self.zones
