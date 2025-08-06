
from flask import Flask, request, jsonify, abort
from datetime import datetime
from typing import Dict, Any, List, Optional
import csv
import os
import random

app = Flask(__name__)

API_PREFIX = "/api/v1.0"

# -------------------------
# In-memory "database"
# -------------------------

MOCK_RAN_CAPABILITIES = {
    "plmns": {("999", "99")},
    "snssai": {("1", "000002"), ("1", "")},  # accept sst=1 with sd '000002' or empty sd
    "qos_profiles": {9},
    "dnns": {"internet"},
}

slice_instances: Dict[str, Dict[str, Any]] = {}
subscription_profiles: Dict[str, Dict[str, Any]] = {}
subscribers: Dict[str, Dict[str, Any]] = {}
groups: Dict[str, List[str]] = {"group1": [], "group2": []}
insertion_order: List[str] = []

# Seed demo data
subscription_profiles["profile"] = {
    "_id": "profile",
    "dnn": "internet",
    "5gQosProfile": {"5qi": 9, "arp": {"priorityLevel": 15, "preemptCap": "NOT_PREEMPT", "preemptVuln": "PREEMPTABLE"}, "priorityLevel": 11},
    "sessionAmbr": {"uplink": "200 Mbps", "downlink": "200 Mbps"},
    "pduSessionTypes": {"defaultSessionType": "IPV4", "allowedSessionTypes": ["IPV4"]},
    "upSecurity": {"upIntegr": "NOT_NEEDED", "upConfid": "NOT_NEEDED"},
}
subscribers["999991000000001"] = {
    "imsi": "999991000000001",
    "msisdn": "999991000000001",
    "k": "000102030405060708090A0B0C0D0E0F",
    "opc": "000102030405060708090A0B0C0D0E0F",
    "sqn": "000000000000",
    "rName": "UE-1",
    "groupName": "group1",
    "ue_static_ipv4_addr": "10.201.0.4/16",
}
groups["group1"].append("999991000000001")
insertion_order.append("999991000000001")

# -------------------------
# Helpers
# -------------------------

def http_404(msg: str):
    resp = jsonify({"detail": msg})
    resp.status_code = 404
    return resp

def http_400(msg: str):
    resp = jsonify({"detail": msg})
    resp.status_code = 400
    return resp

def _validate_slice_against_mock_ran(payload: Dict[str, Any]) -> Optional[str]:
    sp = payload.get("ServiceProfile") or {}
    plmns = sp.get("PLMNIdList") or []
    if not plmns:
        return "PLMNIdList missing"
    ok_plmn = any((str(p.get("mcc")), str(p.get("mnc"))) in MOCK_RAN_CAPABILITIES["plmns"] for p in plmns)
    if not ok_plmn:
        return "PLMN not supported by RAN"

    snssais = sp.get("SNSSAIList") or []
    if not snssais:
        return "SNSSAIList missing"
    ok_snssai = any((str(s.get("sst")), s.get("sd") or "") in MOCK_RAN_CAPABILITIES["snssai"] for s in snssais)
    if not ok_snssai:
        return "SNSSAI not supported by RAN"

    nss = payload.get("NetworkSliceSubnet") or {}
    ep = (nss or {}).get("EpTransport") or {}
    qos_profile = ep.get("qosProfile")
    if qos_profile is not None and qos_profile not in MOCK_RAN_CAPABILITIES["qos_profiles"]:
        return "qosProfile not supported"
    ep_apps = set(ep.get("epApplication") or [])
    if ep_apps and not ep_apps.issubset(MOCK_RAN_CAPABILITIES["dnns"]):
        return "epApplication contains unsupported DNN(s)"

    if sp.get("dnn") and sp.get("dnn") not in MOCK_RAN_CAPABILITIES["dnns"]:
        return "ServiceProfile DNN not supported"
    return None

def _ensure_subscriber_exists(imsi: str) -> Dict[str, Any]:
    ue = subscribers.get(imsi)
    if not ue:
        abort(http_404("Subscriber not found"))
    return ue

def _order_list(lst: List[Dict[str, Any]], order: int) -> List[Dict[str, Any]]:
    if order == -1:
        return list(reversed(lst))
    return lst

def _is_hex32(s: str) -> bool:
    try:
        return isinstance(s, str) and len(s) == 32 and int(s, 16) is not None
    except Exception:
        return False

# -------------------------
# CNC-1: Slice instance
# -------------------------

@app.get(f"{API_PREFIX}/network-slice/slice-instance")
def get_slice_instances():
    return jsonify(list(slice_instances.values()))

@app.post(f"{API_PREFIX}/network-slice/slice-instance")
def add_slice_instance():
    payload = request.get_json(force=True, silent=True) or {}
    if (payload.get("activate_slice") or 0) == 1:
        reason = _validate_slice_against_mock_ran(payload)
        if reason:
            return http_404(reason)
    name = payload.get("sliceName")
    if not name:
        return http_400("sliceName is required")
    slice_instances[name] = payload
    return jsonify({"status": "OK", "sliceName": name})

@app.put(f"{API_PREFIX}/network-slice/slice-instance/<slice_name>")
def update_slice_instance(slice_name: str):
    if slice_name not in slice_instances:
        return http_404("Slice not found")
    payload = request.get_json(force=True, silent=True) or {}
    if (payload.get("activate_slice") or 0) == 1:
        reason = _validate_slice_against_mock_ran(payload)
        if reason:
            return http_404(reason)
    slice_instances[slice_name] = payload
    return jsonify({"status": "OK", "sliceName": slice_name})

@app.delete(f"{API_PREFIX}/network-slice/slice-instance/<slice_name>")
def delete_slice_instance(slice_name: str):
    if slice_name not in slice_instances:
        return http_404("Slice not found")
    del slice_instances[slice_name]
    return jsonify({"status": "OK", "deleted": slice_name})

# -------------------------
# CNC-2: Subscription profile information
# -------------------------

@app.post(f"{API_PREFIX}/cnc-configuration/cnc-subscription-profile")
def create_subscription_profile():
    payload = request.get_json(force=True, silent=True) or {}
    pid = payload.get("_id")
    if not pid:
        return http_400("_id is required")
    if pid in subscription_profiles:
        return http_404("Profile already exists")
    dnn = payload.get("dnn")
    fiveg = (payload.get("5gQosProfile") or {}).get("5qi")
    if dnn not in MOCK_RAN_CAPABILITIES["dnns"] or fiveg not in {5, 9}:
        return http_404("Unsupported dnn or 5qi")
    subscription_profiles[pid] = payload
    return jsonify({"status": "OK", "_id": pid})

@app.get(f"{API_PREFIX}/cnc-configuration/cnc-subscription-profile")
def list_subscription_profiles():
    return jsonify(list(subscription_profiles.values()))

@app.put(f"{API_PREFIX}/cnc-configuration/cnc-subscription-profile/<profile_id>")
def update_subscription_profile(profile_id: str):
    if profile_id not in subscription_profiles:
        return http_404("Profile not found")
    payload = request.get_json(force=True, silent=True) or {}
    dnn = payload.get("dnn")
    fiveg = (payload.get("5gQosProfile") or {}).get("5qi")
    if dnn not in MOCK_RAN_CAPABILITIES["dnns"] or fiveg not in {5, 9}:
        return http_404("Unsupported dnn or 5qi")
    subscription_profiles[profile_id] = payload
    return jsonify({"status": "OK", "_id": profile_id})

@app.delete(f"{API_PREFIX}/cnc-configuration/cnc-subscription-profile/<profile_id>")
def delete_subscription_profile(profile_id: str):
    if profile_id not in subscription_profiles:
        return http_404("Profile not found")
    del subscription_profiles[profile_id]
    return jsonify({"status": "OK", "deleted": profile_id})

# -------------------------
# CNC-4: Subscriber profile Information
# -------------------------

@app.get(f"{API_PREFIX}/cnc-subscriber-management")
def get_subscribers():
    try:
        order = int(request.args.get("order", "1"))
    except Exception:
        order = 1
    lst = [subscribers[imsi] for imsi in insertion_order if imsi in subscribers]
    lst = _order_list(lst, order)
    return jsonify(lst)

@app.post(f"{API_PREFIX}/cnc-subscriber-management")
def add_subscriber():
    payload = request.get_json(force=True, silent=True) or {}
    imsi = payload.get("imsi")
    if not imsi:
        return http_400("imsi is required")
    if imsi in subscribers:
        return http_404("Subscriber already exists")

    gname = payload.get("groupName") or ""
    if gname and gname not in groups:
        return http_404("Unknown group")

    if not _is_hex32(payload.get("k", "")) or not _is_hex32(payload.get("opc", "")):
        return http_404("Invalid K/OPC")

    subscribers[imsi] = payload
    groups.setdefault(gname or "default", [])
    if gname:
        groups[gname].append(imsi)
    insertion_order.append(imsi)
    return jsonify({"status": "OK", "imsi": imsi})

@app.put(f"{API_PREFIX}/cnc-subscriber-management/<imsi>")
def update_subscriber(imsi: str):
    if imsi not in subscribers:
        return http_404("Subscriber not found")
    payload = request.get_json(force=True, silent=True) or {}
    gname = payload.get("groupName") or ""
    if gname and gname not in groups:
        return http_404("Unknown group")
    subscribers[imsi] = payload
    if gname and imsi not in groups[gname]:
        groups[gname].append(imsi)
    return jsonify({"status": "OK", "imsi": imsi})

@app.delete(f"{API_PREFIX}/cnc-subscriber-management/<imsi>")
def delete_subscriber(imsi: str):
    if imsi not in subscribers:
        return http_404("Subscriber not found")
    del subscribers[imsi]
    for g, imsies in groups.items():
        if imsi in imsies:
            imsies.remove(imsi)
    if imsi in insertion_order:
        insertion_order.remove(imsi)
    return jsonify({"status": "OK", "deleted": imsi})

@app.get(f"{API_PREFIX}/cnc-subscriber-management/<imsi>")
def get_single_subscriber(imsi: str):
    return jsonify(_ensure_subscriber_exists(imsi))

@app.get(f"{API_PREFIX}/cnc-subscriber-management/by-group")
def get_subscribers_by_group():
    gname = request.args.get("gname")
    if not gname:
        return http_400("gname is required")
    if gname not in groups:
        return http_404("Group not found")
    try:
        order = int(request.args.get("order", "1"))
    except Exception:
        order = 1
    imsies = groups[gname]
    lst = [subscribers[i] for i in imsies if i in subscribers]
    lst = _order_list(lst, order)
    return jsonify(lst)

@app.get(f"{API_PREFIX}/cnc-subscriber-management/by-batch")
def get_subscribers_by_batch():
    if "start" not in request.args or "end" not in request.args:
        return http_400("start and end are required")
    try:
        start = int(request.args.get("start"))
        end = int(request.args.get("end"))
        order = int(request.args.get("order", "1"))
    except Exception:
        return http_400("start, end and order must be integers")
    ordered = [imsi for imsi in insertion_order if imsi in subscribers]
    if start < 0 or end < 0 or start >= len(ordered) or end > len(ordered):
        return http_404("Range out of bounds")
    selected = ordered[start:end]
    lst = [subscribers[i] for i in selected]
    lst = _order_list(lst, order)
    return jsonify(lst)

@app.get(f"{API_PREFIX}/cnc-subscriber-management/total-count")
def total_count():
    return jsonify({"count": len(subscribers)})

@app.put(f"{API_PREFIX}/cnc-subscriber-management/sqn/<imsi>")
def update_sqn(imsi: str):
    if imsi not in subscribers:
        return http_404("Subscriber not found")
    payload = request.get_json(force=True, silent=True) or {}
    new_sqn = payload.get("sqn")
    if not new_sqn:
        return http_400("sqn missing")
    subscribers[imsi]["sqn"] = new_sqn
    return jsonify({"status": "ok", "imsi": imsi, "sqn": new_sqn})

@app.post(f"{API_PREFIX}/cnc-multisubscriber-management")
def add_multi_subscribers():
    if "size" not in request.args:
        return http_400("size is required")
    try:
        size = int(request.args.get("size"))
    except Exception:
        return http_400("size must be integer")
    if size < 1:
        return http_400("size must be >= 1")
    filename = "esims.csv"
    if not os.path.exists(filename):
        return http_404(f"{filename} not found in working directory")
    added = 0
    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if added >= size:
                break
            imsi = row.get("imsi")
            if not imsi or imsi in subscribers:
                continue
            k = row.get("k", "")
            opc = row.get("opc", "")
            if len(k) != 32 or len(opc) != 32:
                continue
            subscribers[imsi] = row
            insertion_order.append(imsi)
            g = row.get("groupName", "")
            if g:
                groups.setdefault(g, [])
                groups[g].append(imsi)
            added += 1
    return jsonify({"status": "OK", "added": added})

@app.delete(f"{API_PREFIX}/cnc-multisubscriber-management/delete")
def delete_multi_subscribers():
    ids = request.args.get("ids", "")
    if not ids:
        return http_400("ids is required")
    imsis = [i.strip() for i in ids.split(",") if i.strip()]
    deleted = 0
    for imsi in imsis:
        if imsi in subscribers:
            del subscribers[imsi]
            if imsi in insertion_order:
                insertion_order.remove(imsi)
            for g in groups.values():
                if imsi in g:
                    g.remove(imsi)
            deleted += 1
    return jsonify({"status": "ok", "deleted": deleted})


# -------------------------
# In-memory mock data
# -------------------------

MOCK_RAN_CAPABILITIES = {
    "plmns": {("999", "99")},
    "snssai": {("1", "000002"), ("1", "")},
    "qos_profiles": {9},
    "dnns": {"internet"},
}

slice_instances: Dict[str, Dict[str, Any]] = {}
subscription_profiles: Dict[str, Dict[str, Any]] = {}
subscribers: Dict[str, Dict[str, Any]] = {}
groups: Dict[str, List[str]] = {"group1": []}
insertion_order: List[str] = []

# Seed demo entries
subscription_profiles["profile"] = {"_id": "profile", "dnn": "internet", "5gQosProfile": {"5qi": 9}}
subscribers["999991000000001"] = {
    "imsi": "999991000000001",
    "msisdn": "999991000000001",
    "k": "000102030405060708090A0B0C0D0E0F",
    "opc": "000102030405060708090A0B0C0D0E0F",
    "sqn": "000000000000",
    "groupName": "group1"
}
groups["group1"].append("999991000000001")
insertion_order.append("999991000000001")

# -------------------------
# Helpers
# -------------------------

def http_404(msg: str):
    resp = jsonify({"detail": msg})
    resp.status_code = 404
    return resp

def http_400(msg: str):
    resp = jsonify({"detail": msg})
    resp.status_code = 400
    return resp

# -------------------------
# Usage report generator (CNC-15)
# -------------------------

def _generate_usage_report(report_type: str, tgt_ue: str, start: str, end: str):
    if report_type != "ue-usage":
        raise ValueError("Unsupported report-type")
    if not tgt_ue.startswith("imsi-"):
        raise ValueError("tgt_ue must start with 'imsi-'")
    imsi = tgt_ue[5:]
    if imsi not in subscribers:
        raise LookupError("Subscriber not found")
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except Exception:
        raise RuntimeError("Invalid ISO time")
    if end_dt <= start_dt:
        raise RuntimeError("'end' must be after 'start'")
    total_ul = len(imsi) * 12345
    total_dl = len(imsi) * 23456
    return {
        "time_window": {"start": start_dt.isoformat(), "end": end_dt.isoformat()},
        "summary": {"total_uplink_bytes": total_ul, "total_downlink_bytes": total_dl},
    }

# -------------------------
# CNC-15: Performance monitoring data
# -------------------------

@app.get(f"{API_PREFIX}/cnc/monitoring-report-og")
def monitoring_report():
    try:
        rep = _generate_usage_report(request.args["report-type"], request.args["tgt_ue"],
                                     request.args["start"], request.args["end"])
    except (KeyError, ValueError, LookupError) as e:
        return http_404(str(e))
    except RuntimeError as e:
        return http_400(str(e))
    return jsonify(rep)

@app.get(f"{API_PREFIX}/cnc/monitoring-report")
def monitoring_report_transform():
    '''
    Returns throughput/byte metrics plus "timestamp" (end of window).
    Use ?format=csv for CSV instead of JSON.
    '''
    out_fmt = request.args.get("format", "json").lower()
    try:
        rep = _generate_usage_report(request.args["report-type"], request.args["tgt_ue"],
                                     request.args["start"], request.args["end"])
    except (KeyError, ValueError, LookupError) as e:
        return http_404(str(e))
    except RuntimeError as e:
        return http_400(str(e))

    start_dt = datetime.fromisoformat(rep["time_window"]["start"])
    end_dt = datetime.fromisoformat(rep["time_window"]["end"])
    dur = (end_dt - start_dt).total_seconds()

    bytes_sent = rep["summary"]["total_uplink_bytes"] * random.randint(1000, 10000)
    bytes_recv = rep["summary"]["total_downlink_bytes"] * random.randint(1000, 10000)

    sent_mbps = (bytes_sent * 8) / dur / 1_000_000 * random.randint(1000, 10000) * 100
    recv_mbps = (bytes_recv * 8) / dur / 1_000_000 * random.randint(1000, 10000) * 20

    data = {
        "URLLC_Sent_thrp_Mbps": round(sent_mbps, 6),
        "URLLC_BytesSent": bytes_sent,
        "URLLC_BytesReceived": bytes_recv,
        "URLLC_Received_thrp_Mbps": round(recv_mbps, 6),
        "timestamp": end_dt.isoformat(),
    }

    if out_fmt == "csv":
        header = "URLLC_Sent_thrp_Mbps,URLLC_BytesSent,URLLC_BytesReceived,URLLC_Received_thrp_Mbps,timestamp\n"
        row = f'{data["URLLC_Sent_thrp_Mbps"]},{data["URLLC_BytesSent"]},{data["URLLC_BytesReceived"]},{data["URLLC_Received_thrp_Mbps"]},{data["timestamp"]}\n'
        return Response(header + row, mimetype="text/csv")
    return jsonify(data)

# -------------------------
# Entrypoint
# -------------------------

if __name__ == "__main__":
    # Run with: python cumucore-api-engine.py
    app.run(host="0.0.0.0", port=3000)
