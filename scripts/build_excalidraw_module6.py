#!/usr/bin/env python3
"""Build Module 6 Excalidraw scenes with embedded, path-based SVG mathematics.

Requires Typst on PATH. Native Excalidraw shapes/text remain editable; each
formula is a self-contained image with its editable Typst source retained.
"""

from __future__ import annotations

import base64
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagrams/excalidraw/module6"
FORMULAS = {
    "proportion": "p",
    "two-proportions": "p_1 - p_2",
    "mean": "mu",
    "two-means": "mu_1 - mu_2",
    "paired-mean": "mu_d",
    "estimate": "hat(p) = x/n",
    "ci-counts": "n hat(p) >= 10 quad \"and\" quad n(1-hat(p)) >= 10",
    "ht-counts": 'n p_0 >= 10 quad "and" quad n(1-p_0) >= 10',
    "ci-se": '"SE"_"CI" = sqrt((hat(p)(1-hat(p)))/n)',
    "ht-se": '"SE"_0 = sqrt((p_0(1-p_0))/n)',
    "ci-center": '"Center" = hat(p)',
    "ht-center": '"Null center" = p_0',
    "ci-formula": 'hat(p) plus.minus z^* sqrt((hat(p)(1-hat(p)))/n)',
    "test-statistic": 'z_"obs" = (hat(p)-p_0) / sqrt((p_0(1-p_0))/n)',
    "null": 'H_0: p = p_0',
    "alternatives": 'H_a: p > p_0, quad p < p_0, quad "or" quad p != p_0',
    "tail-right": 'p > p_0 : quad P(Z >= z_"obs")',
    "tail-left": 'p < p_0 : quad P(Z <= z_"obs")',
    "tail-two": 'p != p_0 : quad 2 P(Z >= abs(z_"obs"))',
    "decision": '"p-value" <= alpha ?',
}
COLORS = {"ink": "#243247", "blue": "#17628a", "purple": "#6744a0",
          "bluefill": "#e7f3fa", "purplefill": "#f0eafa", "gray": "#f3f5f8",
          "amber": "#fff1d6", "red": "#9c431e", "green": "#e8f5eb",
          "alert": "#b42332", "alertfill": "#fff0f1"}


def render_formulas(names=None) -> dict:
    directory = OUT / "formulas"
    directory.mkdir(parents=True, exist_ok=True)
    rendered = {}
    for name, formula in FORMULAS.items():
        if names is not None and name not in names:
            continue
        source = directory / f"{name}.typ"
        svg_path = directory / f"{name}.svg"
        color = "b42332" if name.endswith("counts") else "243247"
        source.write_text('#set page(width: auto, height: auto, margin: 3pt, fill: none)\n'
                          f'#set text(size: 25pt, fill: rgb("{color}"))\n'
                          f'$ {formula} $\n')
        subprocess.run(["typst", "compile", str(source), str(svg_path)], check=True)
        data = svg_path.read_bytes()
        svg = ET.fromstring(data)
        dims = [float(v) for v in svg.attrib["viewBox"].split()]
        assert b"<path" in data and b"<script" not in data
        rendered[name] = {"svg": data, "width": dims[2], "height": dims[3]}
    return rendered


class Scene:
    def __init__(self, name: str, formulas: dict):
        self.name, self.formulas = name, formulas
        self.elements, self.files = [], {}

    def add(self, kind, id, x, y, w, h, **extra):
        seed = int(hashlib.sha256(id.encode()).hexdigest()[:7], 16)
        element = dict(id=id, type=kind, x=x, y=y, width=w, height=h, angle=0,
                       strokeColor=COLORS["ink"], backgroundColor="transparent",
                       fillStyle="solid", strokeWidth=2, strokeStyle="solid", roughness=0.7,
                       opacity=100, groupIds=[], frameId=None, roundness=None, seed=seed,
                       version=1, versionNonce=seed, isDeleted=False, boundElements=[],
                       updated=1, link=None, locked=False)
        element.update(extra)
        self.elements.append(element)
        return element

    def box(self, id, x, y, w, h, fill="gray", stroke="ink", **extra):
        return self.add("rectangle", id, x, y, w, h, backgroundColor=COLORS.get(fill, fill),
                        strokeColor=COLORS.get(stroke, stroke), roundness={"type": 3}, **extra)

    def text(self, id, text, x, y, w, size=25, color="ink", align="center", group=None):
        return self.add("text", id, x, y, w, size * 1.25 * len(text.splitlines()),
                        text=text, originalText=text, fontSize=size, fontFamily=2,
                        textAlign=align, verticalAlign="top", containerId=None,
                        autoResize=False, lineHeight=1.25, roughness=0,
                        strokeColor=COLORS.get(color, color), groupIds=[group] if group else [])

    def formula(self, name, x, y, w, h, group=None):
        item = self.formulas[name]
        factor = min(w/item["width"], h/item["height"])
        width, height = item["width"]*factor, item["height"]*factor
        file_id = hashlib.sha256(item["svg"]).hexdigest()
        self.files[file_id] = dict(id=file_id, mimeType="image/svg+xml", created=1,
                                  dataURL="data:image/svg+xml;base64," + base64.b64encode(item["svg"]).decode())
        return self.add("image", f"{name}-{len(self.elements)}", x+(w-width)/2, y+(h-height)/2,
                        width, height, fileId=file_id, status="saved", scale=[1, 1], crop=None,
                        groupIds=[group] if group else [],
                        customData={"formulaSource": f"formulas/{name}.typ", "typst": FORMULAS[name]})

    def arrow(self, id, points, color="ink", start=None, end=None):
        x, y = points[0]
        relative = [[px-x, py-y] for px, py in points]
        arrow = self.add("arrow", id, x, y, max(p[0] for p in relative)-min(p[0] for p in relative),
                        max(p[1] for p in relative)-min(p[1] for p in relative), points=relative,
                        startArrowhead=None, endArrowhead="arrow", elbowed=False,
                        strokeColor=COLORS.get(color, color), roughness=0,
                        startBinding=None, endBinding=None)
        for key, target in (("startBinding", start), ("endBinding", end)):
            if target:
                arrow[key] = {"elementId": target["id"], "focus": 0, "gap": 8}
                target["boundElements"].append({"id": id, "type": "arrow"})

    def save(self, directory=OUT):
        # Group each card with its contents so moving it keeps its formulas attached.
        cards = [e for e in self.elements if e["type"] == "rectangle" and not e["id"].endswith("-zone")]
        for e in self.elements:
            if e["type"] not in ("text", "image"):
                continue
            containing = [c for c in cards if e["x"] >= c["x"] and e["y"] >= c["y"]
                          and e["x"]+e["width"] <= c["x"]+c["width"]+0.1
                          and e["y"]+e["height"] <= c["y"]+c["height"]+0.1]
            if containing:
                card = min(containing, key=lambda c:c["width"]*c["height"])
                e["groupIds"] = card["groupIds"] = ["card-"+card["id"]]
        document = dict(type="excalidraw", version=2, source="https://excalidraw.com",
                        elements=self.elements, files=self.files,
                        appState={"viewBackgroundColor": "#ffffff", "gridSize": None})
        ids = {e["id"] for e in self.elements}
        assert len(ids) == len(self.elements)
        for e in self.elements:
            if e["type"] == "image": assert e["fileId"] in self.files
            for b in e["boundElements"]: assert b["id"] in ids
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{self.name}.excalidraw").write_text(json.dumps(document, ensure_ascii=False, indent=2)+"\n")
        return document


def overview(formulas):
    s = Scene("module6-overview", formulas)
    s.text("title", "STAT 250 · Module 6", 50, 35, 1720, 46)
    s.text("subtitle", "Overview", 50, 105, 1720, 30)
    root = s.box("question", 600, 190, 620, 95, "amber")
    s.text("question-text", "What kind of outcome are you studying?", 620, 221, 580, 26)
    for x, name, title, desc, fill, color in [
        (65, "proportions", "PROPORTIONS", "A binary / categorical outcome", "bluefill", "blue"),
        (765, "means", "MEANS", "A quantitative outcome", "purplefill", "purple")]:
        width = 640 if name == "proportions" else 990
        cx = x + width/2
        b = s.box(name, x, 365, width, 105, fill, color)
        s.text(name+"-title", title, x+20, 382, width-40, 30, color)
        s.text(name+"-desc", desc, x+20, 428, width-40, 24)
        s.arrow(name+"-in", [(910,293),(910,325),(cx,325),(cx,357)], start=root, end=b)
    for x, topic, label, desc, formula, color, fill in [
        (50,1,"One proportion", "One population", "proportion","blue","bluefill"),
        (400,2,"Difference in\nproportions", "Two independent groups", "two-proportions","blue","bluefill"),
        (750,3,"One mean", "One population", "mean","purple","purplefill"),
        (1100,4,"Difference in means", "Independent groups\nUnrelated observations", "two-means","purple","purplefill"),
        (1450,5,"Paired differences\nin means", "Same units / matched pairs\nOne difference per pair", "paired-mean","#157364","#e4f5ef")]:
        b = s.box(f"topic{topic}", x, 560, 320, 330, fill, color)
        s.text(f"topic{topic}-title", f"TOPIC {topic}", x+15, 582, 290, 29, color)
        s.text(f"topic{topic}-label", label, x+10, 637, 300, 24)
        s.text(f"topic{topic}-desc", desc, x+10, 718, 300, 20)
        s.formula(formula, x+45, 798, 230, 66)
        parent_x = 385 if topic<3 else 1260
        s.arrow(f"topic{topic}-in", [(parent_x,478),(parent_x,515),(x+160,515),(x+160,552)],color,
                end=b)
    for element in s.elements:
        if element["type"] == "text":
            element["fontFamily"] = 5  # Excalifont, scoped to the overview.
    return s.save()


def detailed(formulas):
    s = Scene("one-proportion-workflow", formulas)
    s.text("title", "STAT 250 · Module 6 · Topic 1", 80, 30, 1440, 39)
    s.text("subtitle", "Normal-based inference for a single proportion", 80, 88, 1440, 28)
    b=s.box("define", 400, 155, 800, 160)
    s.text("define-title", "1  DEFINE THE PARAMETER AND SUMMARIZE THE SAMPLE",420,175,760,24)
    s.text("define-body", "p = population proportion with the designated outcome\nn = sample size; x = observed successes",420,215,760,22)
    s.formula("estimate",650,266,300,40)
    d=s.box("design",400,365,800,150,"alertfill","alert",strokeWidth=3)
    s.text("design-title","2  CHECK THE SAMPLING DESIGN",420,383,760,25,"alert")
    s.text("design-body","Random sample; independent observations.\nWithout replacement: sample small relative to population.\nDoes the design support population inference?",420,426,760,22)
    s.arrow("define-design",[(800,323),(800,357)],start=b,end=d)
    pause=s.box("design-pause",1260,365,320,150,"alertfill","alert")
    s.text("design-pause-text","PAUSE\nResolve the design limitation\nor restrict the conclusion.",1275,395,290,21,"alert")
    s.arrow("design-no",[(1208,440),(1252,440)],"alert",start=d,end=pause)
    s.text("design-no-label","No / unclear",1202,325,180,18,"alert")
    choice=s.box("choose",580,575,440,90,"gray")
    s.text("choose-text","3  WHAT IS THE QUESTION?",600,603,400,25)
    s.arrow("design-yes",[(800,523),(800,567)],start=d,end=choice)
    s.text("design-yes-label","Yes",810,536,70,19)
    # Branch backgrounds make the continuous two-column route easy to follow.
    s.box("ci-zone",35,730,720,1860,"#f6fbfe","#d8e9f2",strokeWidth=1,roughness=0)
    s.box("ht-zone",845,730,720,1860,"#faf7fe","#e4dcef",strokeWidth=1,roughness=0)
    s.text("ci-heading","CONFIDENCE INTERVAL",65,748,660,29,"blue")
    s.text("ht-heading","HYPOTHESIS TEST",875,748,660,29,"purple")
    s.arrow("to-ci",[(690,673),(690,701),(395,701),(395,735)],"blue",start=choice)
    s.arrow("to-ht",[(910,673),(910,701),(1205,701),(1205,735)],"purple",start=choice)
    s.arrow("ci-heading-setup",[(395,795),(395,812)],"blue")
    s.arrow("ht-heading-setup",[(1205,795),(1205,812)],"purple")
    ci=s.box("ci-setup",75,820,640,165,"bluefill","blue")
    s.text("ci-setup-text","Choose confidence level C\nFind z* with middle Normal area C\nFor 95% confidence: z* = 1.96\n(≈ 2 for a quick approximation)",95,842,600,24)
    ht=s.box("ht-setup",885,820,640,165,"purplefill","purple")
    s.formula("null",1000,831,410,42)
    s.formula("alternatives",905,880,600,36)
    s.text("ht-directions","Right-tailed / left-tailed / two-sided",905,920,600,20)
    s.text("ht-alpha","Choose Hₐ from the question; set α.",900,952,610,21)
    for prefix,x,col,count,previous in [("ci",75,"blue","ci-counts",ci),("ht",885,"purple","ht-counts",ht)]:
        check=s.box(prefix+"-counts",x,1025,640,165,"alertfill","alert",strokeWidth=3)
        s.text(prefix+"-counts-title","CHECK " + ("OBSERVED" if prefix=="ci" else "NULL EXPECTED") + " COUNTS",x+20,1045,600,25,"alert")
        s.formula(count,x+30,1088,580,46)
        s.text(prefix+"-counts-note","Both conditions must hold.",x+20,1150,600,22)
        s.arrow(prefix+"-setup-counts",[(x+320,993),(x+320,1017)],col,start=previous,end=check)
        stop=s.box(prefix+"-stop",x,1230,225,110,"alertfill","alert")
        s.text(prefix+"-stop-text","NO → STOP\nReconsider the\nNormal procedure.",x+10,1245,205,21,"alert")
        s.arrow(prefix+"-no",[(x+100,1198),(x+100,1222)],"alert",end=stop)
        s.arrow(prefix+"-yes",[(x+400,1198),(x+400,1372)],col)
        s.text(prefix+"-yes-text","YES",x+415,1250,90,22,col)
    s.box("ci-reference",75,1380,640,235,"bluefill","blue")
    s.text("ci-reference-title","ESTIMATE THE STANDARD ERROR",95,1398,600,25,"blue")
    s.formula("ci-se",155,1436,480,68)
    s.formula("ci-center",225,1515,340,40)
    s.text("ci-center-note","The interval is centered at the observed estimate.\nUse the sample to estimate the standard error.",95,1560,600,22)
    s.box("ht-reference",885,1380,640,235,"purplefill","purple")
    s.text("ht-reference-title","USE THE NULL STANDARD ERROR",905,1398,600,25,"purple")
    s.formula("ht-se",965,1436,480,68)
    s.formula("ht-center",955,1515,500,40)
    s.text("ht-center-note","Under H₀, the sampling distribution of p̂ is\ncentered at the null claim, not the sample estimate.",905,1560,600,22)
    s.arrow("ci-reference-calc",[(395,1623),(395,1672)],"blue")
    s.arrow("ht-reference-calc",[(1205,1623),(1205,1672)],"purple")
    s.box("ci-calculate",75,1680,640,165,"bluefill","blue")
    s.text("ci-calculate-title","CALCULATE THE INTERVAL",95,1700,600,25,"blue")
    s.formula("ci-formula",145,1740,500,78)
    s.box("ht-calculate",885,1680,640,165,"purplefill","purple")
    s.text("ht-calculate-title","STANDARDIZE THE OBSERVED DIFFERENCE",905,1697,600,24,"purple")
    s.formula("test-statistic",970,1738,470,86)
    s.arrow("ci-calc-meaning",[(395,1853),(395,2032)],"blue")
    s.arrow("ht-calc-tail",[(1205,1853),(1205,1892)],"purple")
    s.box("ht-tails",885,1900,640,265,"purplefill","purple")
    s.text("ht-tails-title","FIND THE p-VALUE IN THE DIRECTION OF Hₐ",905,1918,600,23,"purple")
    s.text("ht-z-center","Standardized reference: Z ~ N(0,1), centered at 0.",900,1958,610,21)
    for name,y in [("tail-right",1997),("tail-left",2048),("tail-two",2099)]:
        s.formula(name,930,y,550,44)
    s.box("ci-interpret",75,2040,640,235,"green","blue")
    s.text("ci-interpret-title","INTERPRET THE INTERVAL IN CONTEXT",95,2062,600,25,"blue")
    s.text("ci-interpret-body","We are C% confident that the population\nproportion with [defined outcome] lies\nbetween [lower] and [upper].\n\nKeep the population and outcome explicit.",95,2110,600,25)
    s.arrow("ht-tail-decision",[(1205,2173),(1205,2212)],"purple")
    s.box("ht-decision",1005,2220,400,85,"amber","purple")
    s.formula("decision",1030,2238,350,48)
    s.box("reject",885,2380,300,160,"green","purple")
    s.text("reject-text","YES: Reject H₀\nEvidence supports Hₐ.\nState the direction\nand outcome in context.",900,2402,270,22)
    s.box("fail-reject",1225,2380,300,160,"gray","purple")
    s.text("fail-reject-text","NO: Fail to reject H₀\nInsufficient evidence\nfor Hₐ. This does not\nprove H₀ is true.",1240,2402,270,22)
    s.arrow("decision-yes",[(1105,2313),(1105,2340),(1035,2340),(1035,2372)],"purple")
    s.arrow("decision-no",[(1305,2313),(1305,2340),(1375,2340),(1375,2372)],"purple")
    s.arrow("ci-to-scope",[(395,2283),(395,2625),(650,2625),(650,2652)],"blue")
    s.arrow("ht-to-scope-left",[(1035,2548),(1035,2580),(1205,2580)],"purple")
    s.arrow("ht-to-scope-right",[(1375,2548),(1375,2580),(1205,2580),(1205,2625),(950,2625),(950,2652)],"purple")
    s.box("scope",400,2660,800,90,"green")
    s.text("scope-text","CONCLUDE WITHIN THE STUDY DESIGN",420,2690,760,25)
    for element in s.elements:
        if element["type"] == "text":
            element["fontFamily"] = 5
    return s.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagram", choices=["all", "overview", "detailed"], default="all")
    args = parser.parse_args()
    overview_names = {"proportion", "two-proportions", "mean", "two-means", "paired-mean"}
    names = (overview_names if args.diagram == "overview" else
             set(FORMULAS)-overview_names if args.diagram == "detailed" else None)
    formulas = render_formulas(names)
    scenes = []
    if args.diagram in ("all", "overview"):
        scenes.append(overview(formulas))
    if args.diagram in ("all", "detailed"):
        scenes.append(detailed(formulas))
    # Minimal representative scene for checking SVG import before the full diagrams.
    if args.diagram == "all":
        smoke = Scene("formula-import-check", formulas)
        smoke.box("formula-box",0,0,600,200,"bluefill","blue")
        smoke.text("formula-label","CI: estimate the standard error",20,20,560,26,"blue")
        smoke.formula("ci-se",50,75,500,90)
        smoke.save(ROOT / "build/excalidraw-smoke")
    print(json.dumps({"scenes": [{"elements":len(s["elements"]),"embedded_svg_files":len(s["files"])} for s in scenes]},indent=2))


if __name__ == "__main__":
    main()
