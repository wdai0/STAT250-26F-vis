#!/usr/bin/env python3
"""Build source-grounded Module 6 Topics 2–4 using the approved shared style."""
from __future__ import annotations

import argparse
import json

from build_excalidraw_module6 import FORMULAS, Scene, render_formulas

EXTRA_FORMULAS = {
    't2-estimate': 'hat(p)_1 = x_1/n_1 quad hat(p)_2 = x_2/n_2',
    't2-parameter': 'p_1-p_2 quad "estimated by" quad hat(p)_1-hat(p)_2',
    't2-counts': 'n_i hat(p)_i >= 10 quad "and" quad n_i (1-hat(p)_i) >= 10',
    't2-ci-se': '"SE"_"CI" = sqrt((hat(p)_1 (1-hat(p)_1))/n_1 + (hat(p)_2 (1-hat(p)_2))/n_2)',
    't2-ci-center': '"Center" = hat(p)_1 - hat(p)_2',
    't2-pool': 'hat(p)_p = (x_1+x_2)/(n_1+n_2)',
    't2-ht-se': '"SE"_0 = sqrt(hat(p)_p (1-hat(p)_p)(1/n_1+1/n_2))',
    't2-ht-center': '"Null center" = 0',
    't2-ci': '(hat(p)_1-hat(p)_2) plus.minus z^* "SE"_"CI"',
    't2-stat': 'z_"obs" = ((hat(p)_1-hat(p)_2)-0)/"SE"_0',
    't2-null': 'H_0: p_1-p_2=0',
    't2-alt': 'H_a: p_1-p_2 > 0, quad < 0, quad "or" quad != 0',
    't3-parameter': 'mu quad "estimated by" quad overline(x)',
    't3-df': '"df" = n-1',
    't3-ci-se': '"SE" = s/sqrt(n)',
    't3-ci-center': '"Center" = overline(x)',
    't3-ht-center': '"Null center" = mu_0',
    't3-ci': 'overline(x) plus.minus t^* s/sqrt(n)',
    't3-stat': 't_"obs" = (overline(x)-mu_0)/(s/sqrt(n))',
    't3-null': 'H_0: mu=mu_0',
    't3-alt': 'H_a: mu > mu_0, quad mu < mu_0, quad "or" quad mu != mu_0',
    't4-parameter': 'mu_1-mu_2 quad "estimated by" quad overline(x)_1-overline(x)_2',
    't4-df-terms': 'a=s_1^2/n_1 quad "and" quad b=s_2^2/n_2',
    't4-df-welch': '"df" = (a+b)^2/(a^2/(n_1-1)+b^2/(n_2-1))',
    't4-df-hand': '"df" = min(n_1-1,n_2-1)',
    't4-ci-se': '"SE" = sqrt(s_1^2/n_1+s_2^2/n_2)',
    't4-ci-center': '"Center" = overline(x)_1-overline(x)_2',
    't4-ht-center': '"Null center" = 0',
    't4-ci': '(overline(x)_1-overline(x)_2) plus.minus t^* "SE"',
    't4-stat': 't_"obs" = ((overline(x)_1-overline(x)_2)-0)/"SE"',
    't4-null': 'H_0: mu_1-mu_2=0',
    't4-alt': 'H_a: mu_1-mu_2 > 0, quad < 0, quad "or" quad != 0',
    'z-right': '"Right:" quad P(Z >= z_"obs")',
    'z-left': '"Left:" quad P(Z <= z_"obs")',
    'z-two': '"Two-sided:" quad 2P(Z >= abs(z_"obs"))',
    't-right': '"Right:" quad P(T >= t_"obs")',
    't-left': '"Left:" quad P(T <= t_"obs")',
    't-two': '"Two-sided:" quad 2P(T >= abs(t_"obs"))',
}
FORMULAS.update(EXTRA_FORMULAS)

TOPICS = {
    2: ('two-proportions-workflow', 'Normal-based inference for a difference in proportions'),
    3: ('one-mean-workflow', 't-based inference for a single mean'),
    4: ('two-means-workflow', 't-based inference for a difference in means'),
}


def workflow(topic: int, formulas: dict) -> dict:
    name, subtitle = TOPICS[topic]
    s = Scene(name, formulas)
    prefix = f't{topic}'
    # Topic 4 includes a shared df card; the remaining branch geometry is identical.
    offset = 300 if topic == 4 else 0
    y = lambda value: value + offset
    s.text('title', f'STAT 250 · Module 6 · Topic {topic}', 80, 30, 1440, 39)
    s.text('subtitle', subtitle, 80, 88, 1440, 28)
    s.box('define', 400, 155, 800, 175)
    s.text('define-title', '1  DEFINE THE PARAMETER AND SUMMARIZE THE SAMPLE', 420, 173, 760, 24)
    s.formula(prefix+'-parameter', 440, 213, 720, 43)
    if topic == 2:
        s.formula('t2-estimate', 500, 265, 600, 40)
        s.text('define-note', 'Define success; fix the order: group 1 minus group 2.', 420, 307, 760, 18)
    else:
        note = ('Record n, sample mean, and sample SD s.\nDefine the population, quantitative outcome, and units.' if topic == 3 else
                'Record each sample size, mean, and SD.\nFix the order: group 1 minus group 2; keep the units.')
        s.text('define-note', note, 420, 270, 760, 21)
    s.arrow('define-design', [(800,338),(800,377)])
    s.box('design', 400, 385, 800, 160, 'alertfill', 'alert', strokeWidth=3)
    s.text('design-title', '2  CHECK THE SAMPLING DESIGN', 420, 400, 760, 25, 'alert')
    design = ('Random sample; independent observations.\nWithout replacement: sample small relative to population.\nDoes the design support population inference?' if topic == 3 else
              'Independent groups and observations; random samples.\nWithout replacement: small fraction of each population.\nFix the inference scope supported by the design.')
    s.text('design-body', design, 420, 446, 760, 22)
    s.box('design-pause', 1260, 385, 320, 160, 'alertfill', 'alert')
    s.text('design-pause-text', 'PAUSE\nResolve the design limitation\nor restrict the conclusion.', 1275, 419, 290, 21, 'alert')
    s.arrow('design-no', [(1208,465),(1252,465)], 'alert')
    s.text('design-no-label', 'No / unclear', 1202, 345, 180, 18, 'alert')
    if topic == 4:
        s.arrow('design-df', [(800,553),(800,582)])
        s.text('design-yes', 'Yes', 815, 557, 65, 18)
        s.box('df', 345, 590, 910, 250, 'gray')
        s.text('df-title', 'CHOOSE THE DEGREES OF FREEDOM', 365, 607, 870, 25)
        s.text('df-software', 'Welch–Satterthwaite (software)', 365, 653, 435, 22)
        s.formula('t4-df-terms', 380, 690, 405, 34)
        s.formula('t4-df-welch', 380, 733, 405, 80)
        s.text('df-conservative', 'Conservative hand calculation', 800, 653, 435, 22)
        s.formula('t4-df-hand', 825, 710, 385, 55)
        s.text('df-note', 'Use the chosen df consistently for t* and the p-value.', 370, 812, 860, 18)
        s.arrow('df-choice', [(800,848),(800,887)])
    else:
        s.arrow('design-choice', [(800,553),(800,587)])
        s.text('design-yes', 'Yes', 815, 563, 65, 18)
    s.box('choose', 580, y(595), 440, 90)
    s.text('choose-text', '3  WHAT IS THE QUESTION?', 600, y(623), 400, 25)
    for branch,x,color,fill in [('ci',75,'blue','bluefill'),('ht',885,'purple','purplefill')]:
        cx=x+320
        s.box(branch+'-zone',x-40,y(750),720,2030,
              '#f6fbfe' if branch=='ci' else '#faf7fe', '#d8e9f2' if branch=='ci' else '#e4dcef',strokeWidth=1,roughness=0)
        s.text(branch+'-heading','CONFIDENCE INTERVAL' if branch=='ci' else 'HYPOTHESIS TEST',x-10,y(768),660,29,color)
        s.arrow(branch+'-in',[(690 if branch=='ci' else 910,y(693)),(690 if branch=='ci' else 910,y(721)),(cx,y(721)),(cx,y(755))],color)
        s.arrow(branch+'-to-setup',[(cx,y(815)),(cx,y(832))],color)
        s.box(branch+'-setup',x,y(840),640,185,fill,color)
        if branch=='ci':
            text=('Choose confidence level C\nFind z* with middle Normal area C\nFor 95% confidence: z* = 1.96\n(≈ 2 for a quick approximation)' if topic==2 else
                  'Choose confidence level C\nFind t* with middle t area C\nUse the degrees of freedom below' if topic==3 else
                  'Choose confidence level C\nFind t* with middle t area C\nUse the df method chosen above')
            s.text('ci-setup-text',text,x+20,y(862),600,24)
            if topic==3:s.formula('t3-df',x+160,y(960),320,42)
        else:
            s.formula(prefix+'-null',x+70,y(851),500,44)
            s.formula(prefix+'-alt',x+20,y(903),600,40)
            s.text('ht-directions','Right-tailed / left-tailed / two-sided',x+20,y(951),600,20)
            s.text('ht-alpha','Choose Hₐ from the question; set α.',x+20,y(984),600,21)
        s.arrow(branch+'-setup-check',[(cx,y(1033)),(cx,y(1067))],color)
        s.box(branch+'-conditions',x,y(1075),640,210,'alertfill','alert',strokeWidth=3)
        s.text(branch+'-conditions-title','CHECK OBSERVED COUNTS' if topic==2 else 'CHECK SHAPE AND SAMPLE SIZE',x+20,y(1095),600,24,'alert')
        if topic==2:
            s.formula('t2-counts',x+25,y(1145),590,48)
            s.text(branch+'-conditions-body','For EACH group: i = 1 and i = 2.\nAll four counts must be at least 10.',x+20,y(1211),600,23)
        else:
            body=('Normal population, or n ≥ 30 (course guideline).\nIf n < 30: inspect plots for strong skewness\nand clear outliers; neither should be present.\nCheck influential outliers at every sample size.' if topic==3 else
                  'Both populations Normal, or both n ≥ 30.\nIf either n < 30: inspect BOTH groups;\nno strong skewness or clear outliers.\nCheck influential outliers at every sample size.')
            s.text(branch+'-conditions-body',body,x+20,y(1144),600,21)
        s.arrow(branch+'-no',[(x+100,y(1293)),(x+100,y(1317))],'alert')
        s.box(branch+'-stop',x,y(1325),225,110,'alertfill','alert')
        s.text(branch+'-stop-text','NO → STOP\nReconsider the\n'+('Normal' if topic==2 else 't')+' procedure.',x+10,y(1340),205,21,'alert')
        s.arrow(branch+'-yes',[(x+400,y(1293)),(x+400,y(1472))],color)
        s.text(branch+'-yes-label','YES',x+415,y(1360),90,22,color)
        s.box(branch+'-reference',x,y(1480),640,300,fill,color)
        heading=('ESTIMATE THE UNPOOLED STANDARD ERROR' if branch=='ci' else 'USE THE POOLED NULL STANDARD ERROR') if topic==2 else 'ESTIMATE THE STANDARD ERROR'
        s.text(branch+'-reference-title',heading,x+20,y(1498),600,23,color)
        if topic==2 and branch=='ht':
            s.formula('t2-pool',x+100,y(1542),440,48)
            s.formula('t2-ht-se',x+30,y(1598),580,64)
            s.formula('t2-ht-center',x+125,y(1671),390,36)
            s.text('ht-center-note','Under equality, the difference is centered at 0.\nPool successes to estimate the common proportion.',x+20,y(1720),600,20)
        else:
            s.formula(prefix+'-ci-se',x+35,y(1550),570,78)
            s.formula(prefix+'-'+branch+'-center',x+60,y(1640),520,44)
            if branch=='ci': note='The interval is centered at the observed estimate.\nUse the sample data to estimate the standard error.'
            elif topic==3: note='Under H₀, the sample mean is centered at μ₀.\nUse s to estimate the unknown population SD.'
            else: note='Under H₀, the difference is centered at 0.\nEstimate each group variance separately.'
            s.text(branch+'-center-note',note,x+20,y(1710),600,21)
        s.arrow(branch+'-reference-calc',[(cx,y(1788)),(cx,y(1832))],color)
        s.box(branch+'-calculate',x,y(1840),640,170,fill,color)
        s.text(branch+'-calculate-title','CALCULATE THE INTERVAL' if branch=='ci' else 'STANDARDIZE THE OBSERVED DIFFERENCE',x+20,y(1858),600,24,color)
        s.formula(prefix+('-ci' if branch=='ci' else '-stat'),x+45,y(1905),550,80)
    s.arrow('ci-calc-interpret',[(395,y(2018)),(395,y(2187))],'blue')
    s.box('ci-interpret',75,y(2195),640,250,'green','blue')
    s.text('ci-interpret-title','INTERPRET THE INTERVAL IN CONTEXT',95,y(2215),600,25,'blue')
    interpretation=('We are C% confident that p₁ − p₂ lies\nbetween [lower] and [upper].\nState the groups and success category.\nPositive values mean group 1 is higher.' if topic==2 else
                    'We are C% confident that the population\nmean lies between [lower] and [upper].\nState the population, outcome, and units.' if topic==3 else
                    'We are C% confident that μ₁ − μ₂ lies\nbetween [lower] and [upper].\nState the groups, outcome, and units.\nPositive values mean group 1 is higher.')
    s.text('ci-interpret-body',interpretation,95,y(2270),600,24)
    s.arrow('ht-calc-tails',[(1205,y(2018)),(1205,y(2052))],'purple')
    s.box('ht-tails',885,y(2060),640,280,'purplefill','purple')
    s.text('ht-tails-title','FIND THE p-VALUE IN THE DIRECTION OF Hₐ',905,y(2078),600,23,'purple')
    reference=('Z ~ N(0,1), centered at 0.' if topic==2 else 'T follows t with df = n − 1, centered at 0.' if topic==3 else 'T follows t with the chosen df, centered at 0.')
    s.text('ht-reference-distribution',reference,900,y(2120),610,21)
    for tail,yy in [('right',2164),('left',2216),('two',2268)]:
        s.formula(('z' if topic==2 else 't')+'-'+tail,930,y(yy),550,44)
    s.arrow('ht-tails-decision',[(1205,y(2348)),(1205,y(2382))],'purple')
    s.box('decision',1005,y(2390),400,85,'amber','purple')
    s.formula('decision',1030,y(2408),350,48)
    for x,yes in [(885,True),(1225,False)]:
        s.box('reject' if yes else 'fail-reject',x,y(2550),300,160,'green' if yes else 'gray','purple')
        s.text('reject-text' if yes else 'fail-reject-text',
               'YES: Reject H₀\nEvidence supports Hₐ.\nState the direction\nand outcome in context.' if yes else
               'NO: Fail to reject H₀\nInsufficient evidence\nfor Hₐ. This does not\nprove H₀ is true.',x+15,y(2572),270,22)
        startx=1105 if yes else 1305
        s.arrow('decision-yes' if yes else 'decision-no',[(startx,y(2483)),(startx,y(2510)),(x+150,y(2510)),(x+150,y(2542))],'purple')
    s.arrow('ci-end',[(395,y(2453)),(395,y(2810)),(650,y(2810)),(650,y(2842))],'blue')
    s.arrow('ht-merge-left',[(1035,y(2718)),(1035,y(2750)),(1205,y(2750))],'purple')
    s.arrow('ht-end',[(1375,y(2718)),(1375,y(2750)),(1205,y(2750)),(1205,y(2810)),(950,y(2810)),(950,y(2842))],'purple')
    s.box('scope',400,y(2850),800,90,'green')
    s.text('scope-text','CONCLUDE WITHIN THE STUDY DESIGN',420,y(2880),760,25)
    for element in s.elements:
        if element['type']=='text': element['fontFamily']=5
    return s.save()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topic',choices=['2','3','4','all'],default='all')
    args=parser.parse_args()
    topics=[2,3,4] if args.topic=='all' else [int(args.topic)]
    names={name for name in EXTRA_FORMULAS if any(name.startswith(f't{t}-') for t in topics)}
    names |= {'decision'} | {f'{ref}-{tail}' for ref in ('z','t') for tail in ('right','left','two')}
    formulas=render_formulas(names)
    scenes=[workflow(topic,formulas) for topic in topics]
    print(json.dumps([{'diagram':TOPICS[t][0],'elements':len(d['elements']),'svg_files':len(d['files'])}
                      for t,d in zip(topics,scenes)],indent=2))


if __name__=='__main__': main()
