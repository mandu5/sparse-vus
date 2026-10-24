"""Prospective full-precision stored-score study; commands have separate receipts.

Freeze selects raw series without metrics. Generate saves unrounded scores.
Run checks frozen sources/inputs before serial balanced complete-call timing.
The study is an evaluator workload, not a detector-accuracy leaderboard.
"""
from __future__ import annotations
import os
for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[key] = "1"
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import statistics
import sys
import time
import warnings
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/pvldb-research-20261024/full-precision"
CACHE = ROOT / ".cache/pvldb-full-precision-20261024"
ARCHIVE = ROOT / "cache/TSB-AD-U.zip"
ARCHIVE_SHA = "0c47020d3423723c70773736dbd800369f2b487328becbf339450d1ae5020961"
MODELS = ["isolation_forest", "local_outlier_factor", "knn_distance", "one_class_svm",
          "pca_reconstruction", "kmeans_distance", "histogram_density", "shrinkage_mahalanobis"]
METHODS = ["released", "geometry", "stream", "saturation", "dense", "external"]
SOURCES = ["experiments/pvldb_full_precision.py", "experiments/fast_vus_adapter.py",
           "src/sparse_vus/batch.py", "src/sparse_vus/core.py", "src/sparse_vus/radix.py",
           "src/sparse_vus/compiled.py", "src/sparse_vus/pr_compiled.py",
           "src/sparse_vus/dense_radix.py", "src/sparse_vus/saturation.py",
           "src/sparse_vus/sampling.py", ".cache/fast_vus/fast_vus.py"]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        while data:=f.read(1<<20): h.update(data)
    return h.hexdigest()


def write_new(path, value):
    with Path(path).open("x") as f:
        json.dump(value,f,indent=2,allow_nan=False); f.write("\n")


def winners(values):
    values=np.asarray(values,float)
    return np.flatnonzero(values >= np.max(values)-1e-10).tolist()


def paired_summary(candidate, baseline, *, seed=20261024):
    candidate,baseline=np.asarray(candidate,float),np.asarray(baseline,float)
    if candidate.shape!=baseline.shape or candidate.ndim!=1 or not len(candidate):
        raise ValueError("paired nonempty arrays required")
    if np.any(candidate<=0) or np.any(baseline<=0):
        raise ValueError("positive runtimes required")
    logs=np.log(baseline/candidate)
    rng=np.random.default_rng(seed)
    draws=logs[rng.integers(0,len(logs),size=(10000,len(logs)))].mean(axis=1)
    return {"geometric_speedup":float(np.exp(logs.mean())),
            "ci95":np.exp(np.quantile(draws,[.025,.975])).tolist(),
            "ci_familywise95_3collections":np.exp(np.quantile(draws,[.05/6,1-.05/6])).tolist(),
            "case_wins":int(np.sum(logs>0)),"cases":len(logs),
            "minimum_speedup":float(np.exp(logs.min())),
            "maximum_speedup":float(np.exp(logs.max()))}


def generate_scores(observations):
    """Eight fixed unsupervised families on trailing windows; labels absent.

    Every time point receives a score. Leading windows repeat the first value.
    Fitting uses at most 2048 evenly spaced windows from the complete unlabeled
    series (offline/transductive). No rounding, jitter, clipping or min-max score
    normalization. Reference-window standardization is shared across models.
    """
    from sklearn.ensemble import IsolationForest
    from sklearn.neighbors import LocalOutlierFactor, NearestNeighbors
    from sklearn.svm import OneClassSVM
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.covariance import LedoitWolf
    from threadpoolctl import threadpool_limits
    x=np.asarray(observations,dtype=np.float64)
    if x.ndim!=1 or len(x)<2 or not np.isfinite(x).all():
        raise ValueError("finite one-dimensional observations, length >=2 required")
    width=16
    windows=np.lib.stride_tricks.sliding_window_view(np.pad(x,(width-1,0),mode="edge"),width)
    indices=np.linspace(0,len(x)-1,min(2048,len(x))).astype(np.int64)
    reference=windows[indices]
    mean=reference.mean(axis=0); std=reference.std(axis=0); std[std==0]=1.
    data=np.ascontiguousarray((windows-mean)/std)
    train=data[indices]
    scores=[]; records={}
    with threadpool_limits(limits=1):
        for model in MODELS:
            start=time.perf_counter()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                if model=="isolation_forest":
                    estimator=IsolationForest(n_estimators=100,max_samples=min(256,len(train)),
                                              random_state=20261024,n_jobs=1).fit(train)
                    values=-estimator.score_samples(data)
                elif model=="local_outlier_factor":
                    estimator=LocalOutlierFactor(n_neighbors=min(20,len(train)-1),novelty=True,
                                                  n_jobs=1).fit(train)
                    values=-estimator.score_samples(data)
                elif model=="knn_distance":
                    estimator=NearestNeighbors(n_neighbors=min(20,len(train)),n_jobs=1).fit(train)
                    values=estimator.kneighbors(data,return_distance=True)[0][:,-1]
                elif model=="one_class_svm":
                    estimator=OneClassSVM(kernel="rbf",gamma=1/width,nu=.05).fit(train)
                    values=-estimator.score_samples(data)
                elif model=="pca_reconstruction":
                    estimator=PCA(n_components=min(8,len(train)-1,width-1),svd_solver="full").fit(train)
                    residual=data-estimator.inverse_transform(estimator.transform(data))
                    values=np.mean(residual*residual,axis=1)
                elif model=="kmeans_distance":
                    estimator=KMeans(n_clusters=min(16,len(train)),n_init=1,max_iter=100,
                                     random_state=20261024).fit(train)
                    values=estimator.transform(data).min(axis=1)
                elif model=="histogram_density":
                    values=np.zeros(len(data))
                    for col in range(width):
                        hist,edges=np.histogram(train[:,col],bins=20)
                        cell=np.clip(np.searchsorted(edges,data[:,col],side="right")-1,0,19)
                        values-=np.log((hist[cell]+1)/(len(train)+20))
                elif model=="shrinkage_mahalanobis":
                    estimator=LedoitWolf().fit(train)
                    values=estimator.mahalanobis(data)
                values=np.asarray(values,np.float64)
            elapsed=time.perf_counter()-start
            if values.shape!=(len(x),) or not np.isfinite(values).all():
                raise ValueError(f"invalid output: {model}")
            scores.append(values)
            records[model]={"seconds":elapsed,"distinct":int(len(np.unique(values))),
                            "warnings":[str(w.message) for w in caught]}
    return np.stack(scores),records


def freeze():
    import pandas as pd
    if sha(ARCHIVE)!=ARCHIVE_SHA: raise ValueError("raw archive changed")
    OUT.mkdir(parents=True,exist_ok=False)
    development=json.loads((ROOT/"artifacts/pvldb-research-20261024/development/protocol.json").read_text())
    dev={r["series"] for r in development["cases"]}
    old=set(json.loads((ROOT/"artifacts/selected_series.json").read_text())["ordered_series"])
    cases=[]; exclusions=[]; hashes=set()
    with zipfile.ZipFile(ARCHIVE) as z:
        for path in sorted(z.namelist()):
            if not path.endswith(".csv"): continue
            family=next((f for f in ("NAB","SMAP","SMD") if f"_{f}_" in path),None)
            if family is None: continue
            name=Path(path).stem
            reason="development series" if name in dev else ("source-labelled synthetic" if "_Synthetic_" in name else None)
            if reason:
                exclusions.append({"series":name,"reason":reason}); continue
            raw=z.read(path); frame=pd.read_csv(io.BytesIO(raw))
            x=frame["Data"].to_numpy(dtype=np.float64); y=frame["Label"].to_numpy()
            if len(x)<2 or not np.isfinite(x).all() or not np.isin(y,[0,1]).all() or not 0<y.sum()<len(y):
                raise ValueError(f"invalid raw case (no silent exclusion): {name}")
            identity=hashlib.sha256(x.tobytes()+y.astype(np.int8).tobytes()).hexdigest()
            if identity in hashes:
                exclusions.append({"series":name,"reason":"exact observation+label duplicate"}); continue
            hashes.add(identity)
            cases.append({"series":name,"family":family,"member":path,"n":len(x),
                          "positive_points":int(y.sum()),"raw_sha256":hashlib.sha256(raw).hexdigest(),
                          "observation_label_identity":identity,"raw_recording_previously_measured_by_name":name in old})
    methods=list(METHODS)
    # Two balanced Latin blocks; each method appears twice in every position.
    orders=[methods[i:]+methods[:i] for i in range(len(methods))]
    orders += [list(reversed(order)) for order in orders]
    protocol={"status":"FROZEN_BEFORE_NEW_SCORE_OR_METRIC_OUTCOMES",
              "created_utc":datetime.now(timezone.utc).isoformat(),"source_commit_before_additions":"92319eafd0f937a152edf3a5c7e4355b2114acce",
              "archive_url":"https://www.thedatum.org/datasets/TSB-AD-U.zip","archive_sha256":ARCHIVE_SHA,
              "source_sha256":{p:sha(ROOT/p) for p in SOURCES},"cases":cases,"exclusions":exclusions,
              "collections":["NAB","SMAP","SMD"],"models":MODELS,"methods":methods,
              "widths":[30,100],"primary_width":30,"repetitions":len(orders),"orders":orders,
              "bootstrap":"10000 paired series resamples of log ratios of case median complete-call times; per-collection, plus Bonferroni 3-collection bounds; seed20261024",
              "model_protocol":"8 distinct unsupervised CPU families; trailing16 windows; edge-repeat initial values; fit2048 evenly spaced unlabeled windows from complete series; fixed seed20261024; full float64 scores. Exact parameters bound by driver source.",
              "failure_policy":"no replacement/exclusion after scores; nonfinite outputs halt; warnings and constant outputs retained",
              "reused_data":"Physical recording reuse is explicit; new detector scores are prospectively generated. Excludes only six development names and source-labelled Synthetic rows; exact within-panel observation+label duplicates logged. Cross-catalogue normalized/endpoint-shift identity is not exhaustively excluded.",
              "parity_atol":1e-11,"winner_tie_atol":1e-10,
              "timing":"Single process/thread; all public validation, geometry, sorting, allocation, widths and winner selection included. Repeated in-memory complete-call cases plus separate file-read-to-JSON-write collection passes. No detector fitting in stored-score time. Imports/JIT excluded equally. No fsync/cold-disk claim.",
              "confirmatory_candidate":"stream; selected on development corpus before new scores",
              "primary_success":"same numerical winner sets; max pairwise error<=1e-11; candidate faster than every eligible external exact method on all3collections with familywise CI lower>1; report released and saturation internal controls without exclusion"}
    write_new(OUT/"protocol.json",protocol)
    print(json.dumps({"protocol_sha256":sha(OUT/"protocol.json"),"cases":len(cases),
                      "collections":{f:sum(r['family']==f for r in cases) for f in protocol['collections']},
                      "previously_measured":sum(r['raw_recording_previously_measured_by_name'] for r in cases)},indent=2))


def verify_protocol():
    p=json.loads((OUT/"protocol.json").read_text())
    for name,expected in p["source_sha256"].items():
        if sha(ROOT/name)!=expected: raise ValueError(f"frozen source changed: {name}")
    if sha(ARCHIVE)!=p["archive_sha256"]: raise ValueError("archive changed")
    return p


def generate():
    import pandas as pd
    import sklearn
    p=verify_protocol(); CACHE.mkdir(parents=True,exist_ok=False)
    receipts=[]
    with zipfile.ZipFile(ARCHIVE) as z, (OUT/"generation.jsonl").open("x") as log:
        for index,case in enumerate(p["cases"]):
            raw=z.read(case["member"])
            if hashlib.sha256(raw).hexdigest()!=case["raw_sha256"]: raise ValueError("member changed")
            frame=pd.read_csv(io.BytesIO(raw)); x=frame["Data"].to_numpy(dtype=np.float64)
            y=frame["Label"].to_numpy(dtype=np.int8)
            scores,details=generate_scores(x)
            file=CACHE/f"{index:04d}.npz"
            with file.open("xb") as f: np.savez(f,observations=x,labels=y,scores=scores)
            row={**case,"file":file.name,"npz_sha256":sha(file),"bytes":file.stat().st_size,
                 "score_sha256":hashlib.sha256(scores.tobytes()).hexdigest(),"models":details}
            receipts.append(row); log.write(json.dumps(row,allow_nan=False)+"\n"); log.flush()
            print(index+1,len(p["cases"]),case["series"],flush=True)
    write_new(OUT/"inputs.json",{"status":"COMPLETE","protocol_sha256":sha(OUT/"protocol.json"),
              "python":sys.version,"numpy":np.__version__,"sklearn":sklearn.__version__,"pandas":pd.__version__,
              "series":receipts,"metric_outcomes_computed":False})


def evaluate(method,y,scores,width):
    from sparse_vus.batch import batch_pr
    from sparse_vus.radix import sparse_pr_radix_jit
    from sparse_vus.saturation import sparse_pr_saturation_jit
    from sparse_vus.dense_radix import dense_pr_nearest_radix_jit
    from fast_vus_adapter import fast_vus_pr
    if method in ("geometry","stream"):
        values=batch_pr(y,scores,width,strategy=method)
    else:
        f={"released":sparse_pr_radix_jit,"saturation":sparse_pr_saturation_jit,
           "dense":dense_pr_nearest_radix_jit,
           "external":lambda y,s,w:fast_vus_pr(y,s,w,len(y))}[method]
        values=np.asarray([f(y,s,width) for s in scores])
    return values,winners(values)


def run():
    sys.path[:0]=[str(ROOT/"src"),str(ROOT/"experiments")]
    p=verify_protocol(); inputs=json.loads((OUT/"inputs.json").read_text())
    if inputs["protocol_sha256"]!=sha(OUT/"protocol.json"): raise ValueError("input/protocol mismatch")
    for case in inputs["series"]:
        if sha(CACHE/case["file"])!=case["npz_sha256"]: raise ValueError("array changed")
    write_new(OUT/"run-start.json",{"utc":datetime.now(timezone.utc).isoformat(),"platform":platform.platform(),
              "python":sys.version,"numpy":np.__version__,"protocol_sha256":sha(OUT/"protocol.json"),
              "inputs_sha256":sha(OUT/"inputs.json")})
    y=np.asarray([0,1,0,0,1,0],np.int8); s=np.tile(np.arange(6.,dtype=float),(8,1))
    for method in METHODS: evaluate(method,y,s,30)
    with (OUT/"records.jsonl").open("x") as log:
        for case in inputs["series"]:
            with np.load(CACHE/case["file"],allow_pickle=False) as z:
                y=z["labels"]; scores=z["scores"]
            for width in p["widths"]:
                expected,expected_winners=evaluate("released",y,scores,width)
                for trial,order in enumerate(p["orders"]):
                    for method in order:
                        start=time.perf_counter_ns(); values,selected=evaluate(method,y,scores,width)
                        elapsed=(time.perf_counter_ns()-start)*1e-9
                        error=float(np.max(np.abs(values-expected)))
                        if error>p["parity_atol"] or selected!=expected_winners:
                            raise ValueError(f"parity failure: {case['series']}, {method}, {width}, {error}")
                        row={"series":case["series"],"family":case["family"],"width":width,
                             "method":method,"trial":trial,"seconds":elapsed,"max_error":error,
                             "values":values.tolist(),"winners":selected}
                        log.write(json.dumps(row,allow_nan=False)+"\n"); log.flush()
            print(case["series"],"timed",flush=True)
    # Full collection operations, measured directly rather than summed case medians.
    with (OUT/"workflows.jsonl").open("x") as log:
        for family in p["collections"]:
            cases=[c for c in inputs["series"] if c["family"]==family]
            for trial,order in enumerate(p["orders"]):
                for method in order:
                    target=CACHE/"last-workflow-output.json"
                    start=time.perf_counter_ns(); decisions=[]
                    for case in cases:
                        with np.load(CACHE/case["file"],allow_pickle=False) as z:
                            values,selected=evaluate(method,z["labels"],z["scores"],30)
                        decisions.append({"series":case["series"],"values":values.tolist(),"winners":selected})
                    with target.open("w") as f: json.dump(decisions,f,allow_nan=False)
                    seconds=(time.perf_counter_ns()-start)*1e-9
                    log.write(json.dumps({"family":family,"trial":trial,"method":method,"seconds":seconds,
                                          "decisions":decisions})+"\n"); log.flush()
            print(family,"workflow complete",flush=True)
    write_new(OUT/"run-complete.json",{"status":"COMPLETE","records_sha256":sha(OUT/"records.jsonl"),
               "workflows_sha256":sha(OUT/"workflows.jsonl"),"completed_utc":datetime.now(timezone.utc).isoformat()})
    report()


def report():
    p=verify_protocol(); inputs=json.loads((OUT/"inputs.json").read_text())
    receipt=json.loads((OUT/"run-complete.json").read_text())
    for file in ("records","workflows"):
        if sha(OUT/f"{file}.jsonl")!=receipt[f"{file}_sha256"]: raise ValueError("record digest mismatch")
    rows=[json.loads(s) for s in (OUT/"records.jsonl").read_text().splitlines()]
    workflows=[json.loads(s) for s in (OUT/"workflows.jsonl").read_text().splitlines()]
    expected={(c["series"],w,m,t) for c in p["cases"] for w in p["widths"] for m in METHODS for t in range(p["repetitions"])}
    actual=[(r["series"],r["width"],r["method"],r["trial"]) for r in rows]
    if len(actual)!=len(expected) or set(actual)!=expected: raise ValueError("incomplete or duplicate records")
    summaries={}
    for width in p["widths"]:
        for family in p["collections"]:
            series=[r["series"] for r in p["cases"] if r["family"]==family]
            med={m:[statistics.median(r["seconds"] for r in rows if r["series"]==s and r["width"]==width and r["method"]==m) for s in series] for m in METHODS}
            summaries[f"{family}_L{width}"]={m:paired_summary(med["stream"],med[m]) for m in METHODS if m!="stream"}
    workflow_summary={}
    for family in p["collections"]:
        times={m:[r["seconds"] for r in workflows if r["family"]==family and r["method"]==m] for m in METHODS}
        if any(len(t)!=p["repetitions"] for t in times.values()): raise ValueError("incomplete workflows")
        median={m:statistics.median(t) for m,t in times.items()}
        workflow_summary[family]={"median_seconds":median,"all_seconds":times,
                                   "baseline_over_stream":{m:median[m]/median["stream"] for m in METHODS},
                                   "paired_trial_uncertainty":{m:paired_summary(times["stream"],times[m])
                                                               for m in METHODS if m!="stream"}}
    # Verify decisions after the full operation clocks, rather than within only one method.
    decisions={}
    for row in workflows:
        for case in row["decisions"]:
            if case["series"] in decisions and decisions[case["series"]]!=case["winners"]:
                raise ValueError("workflow winners disagree")
            decisions[case["series"]]=case["winners"]
    result={"status":"COMPLETE","protocol_sha256":sha(OUT/"protocol.json"),
            "inputs_sha256":sha(OUT/"inputs.json"),"records_sha256":receipt["records_sha256"],
            "workflows_sha256":receipt["workflows_sha256"],"series":len(p["cases"]),
            "score_vectors":len(p["cases"])*len(MODELS),"scalar_error_max":max(r["max_error"] for r in rows),
            "all_workflow_winner_sets_agree":True,"case_paired_summaries":summaries,"workflows":workflow_summary,
            "distinct_values":{"min":min(d["distinct"] for c in inputs["series"] for d in c["models"].values()),
                               "max":max(d["distinct"] for c in inputs["series"] for d in c["models"].values())},
            "claims":"New detector outputs on explicit partly reused raw collections; numerical exhaustive equality, not real-arithmetic certification; no external adoption or acceptance inferred."}
    write_new(OUT/"report.json",result)
    print(json.dumps({"series":result["series"],"scalar_error_max":result["scalar_error_max"],
                      "case_paired_summaries":summaries},indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=["freeze","generate","run","report"])
    globals()[parser.parse_args().command]()
