import json, os, boto3, numpy as np
bedrock   = boto3.client("bedrock-runtime")
ts_q      = boto3.client("timestream-query")

DB  = os.getenv("DB_NAME")
TBL = os.getenv("TABLE")
MODEL_ID = os.getenv("MODEL_ID")

def fetch_latest(series: str, hours: int = 168):
    q = (f"SELECT measure_value::double AS val, time "
         f"FROM \"{DB}\".\"{TBL}\" "
         f"WHERE measure_name = '{series}' "
         f"AND time > ago({hours}h)")
    rows = ts_q.query(QueryString=q)["Rows"]
    return [float(r['Data'][0]['ScalarValue']) for r in rows]

def summarise(gluc, wt, bp_sys, bp_dia):
    return (f"Avg glucose 7d: {np.mean(gluc):.1f} mg/dL "
            f"(sd {np.std(gluc):.1f}). "
            f"Weight change 30d: {wt[-1] - wt[0]:+.1f} kg. "
            f"Latest BP: {bp_sys[-1]}/{bp_dia[-1]} mmHg.")

def handler(event, _):
    body  = json.loads(event["body"])
    userQ = body["prompt"]

    g,w,sys,dia = (fetch_latest("glucose"),
                   fetch_latest("weight"),
                   fetch_latest("bp_sys"),
                   fetch_latest("bp_dia"))

    context = summarise(g,w,sys,dia)
    payload = {
        "messages": [
            {"role":"system",
             "content":"You are a helpful clinical assistant."},
            {"role":"user", "content":userQ},
            {"role":"assistant", "name":"vitals", "content":context}
        ],
        "max_tokens": 400
    }
    resp = bedrock.invoke_model(modelId=MODEL_ID,
                                body=json.dumps(payload).encode())
    answer = json.loads(resp['body'].read())['content']
    return {"statusCode":200,
            "headers":{"Content-Type":"application/json"},
            "body":json.dumps({"answer":answer})}
