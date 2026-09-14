import json, math, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'python'))
from analyze import run, counting, validate, DEFAULTS, DATA, error_metrics
from extensions import match_events

class ProjectTests(unittest.TestCase):
    def test_audit_raw_and_unique(self):
        r=run('audit',{'year':'all'})
        self.assertEqual(r['metrics']['原始行'],48204)
        self.assertEqual(r['metrics']['不同小时'],40575)
        self.assertEqual(r['metrics']['重复行'],7629)
        self.assertEqual(sum(x[1] for x in r['rows']),40575)
        self.assertEqual(sum(x[2] for x in r['rows']),48204)

    def test_forecast_common_samples(self):
        for h in ['1','3','6']:
            r=run('forecast',{'horizon':h})
            self.assertTrue(all(x[1]==r['metrics']['有效测试样本'] for x in r['rows']))
            self.assertTrue(all('2018-07'<=x[0]<'2018-10' for x in r['exportRows']))
            self.assertTrue(all(math.isfinite(x[2]) for x in r['rows']))
        self.assertEqual(error_metrics([],2),[0,None,None,None])

    def test_spatial_conservation(self):
        for cell in ['250','500','1000']:
            r=run('hotspots',{'cell':cell})
            self.assertEqual(sum(x[1] for x in r['rows']),r['metrics']['可落图记录'])
            self.assertEqual(r['metrics']['可落图记录']+r['metrics']['坐标排除'],r['metrics']['筛选记录'])

    def test_taxi_denominators(self):
        self.assertEqual(run('taxi')['metrics']['筛选上车记录'],56549)
        self.assertEqual(run('taxi',{'day':'weekend'})['metrics']['日期数'],8)
        self.assertEqual(run('taxi',{'day':'weekday'})['metrics']['日期数'],23)
        night=run('taxi',{'period':'night'})['metrics']['筛选上车记录']
        day=run('taxi',{'period':'day'})['metrics']['筛选上车记录']
        self.assertEqual(night+day,56549)

    def test_counting_one_event_per_id_and_direction(self):
        data={'rows':[['a',i*100,x,0,'car'] for i,x in enumerate([-1,0.1,1,.1,-1,1])]}
        c={**DEFAULTS['counting'],'line':'0','band':'.3'}
        r=counting(data,c)
        self.assertEqual(r['metrics']['跨线事件'],2)
        self.assertEqual(r['metrics']['正方向事件'],1)
        self.assertEqual(r['metrics']['负方向事件'],1)

    def test_counting_no_bridge_over_gap(self):
        data={'rows':[['a',0,-1,0,'car'],['a',2000,1,0,'car']]}
        r=counting(data,{**DEFAULTS['counting'],'line':'0','gap':'1.5'})
        self.assertEqual(r['metrics']['跨线事件'],0)

    def test_counting_real_event_identity(self):
        r=run('counting');events=r['rows']
        self.assertGreater(len(events),0)
        self.assertEqual(len(events),len({(e[0],e[2]) for e in events}))
        self.assertTrue(all(0<=e[1]<120 for e in events))

    def test_manual_matching_is_one_to_one(self):
        predicted=[['1',1.1,'+x'],['1',1.2,'+x'],['2',3,'-x']]
        truth=[{'track_id':'1','time_s':'1','direction':'+x'},{'track_id':'3','time_s':'4','direction':'-x'}]
        metrics,*_=match_events(predicted,truth,.5)
        self.assertEqual([metrics[k] for k in ['tp','fp','fn']],[1,2,1])
        self.assertEqual(match_events([],[])[0]['precision'],None)

    def test_invalid_configuration(self):
        for project,config in [('counting',{'gap':'nan'}),('forecast',{'horizon':'-1'}),('taxi',{'normalize':'bad'}),('audit',{'oops':'1'})]:
            with self.assertRaises(ValueError):validate(project,config)

if __name__=='__main__':unittest.main()
