import json
import requests
import os
import pandas as pd
from flask import Flask, Response
from io import StringIO

DREAMHOST_ACCESS_KEY = os.environ.get('DREAMHOST_ACCESS_KEY')
DREAMHOST_URL = "https://api.dreamhost.com" 
CONTENT_TYPE = 'application/external.dns.webhook+json;version=1'

app = Flask(__name__)

# Functions tomake requests to the Dreamhost API using an access token generated from:
# > https://panel.dreamhost.com/index.cgi?tree=home.api

def lst_zones():
    """List all DNS zones"""
    response = requests.get(DREAMHOST_URL, params={
        'cmd': 'dns-list_records',
        'key': DREAMHOST_ACCESS_KEY,
    })
    if response.status_code != 200:
        raise RuntimeError("did not receive a response")
    
    df = pd.read_csv(StringIO(response.text.removeprefix("success\n")), sep='\t')
    df = df[df['editable']==1][['zone']]

    summary = []
    for z in sorted(df['zone'].unique()):
        summary.append(f"*.{z}")
    return json.dumps(summary)

def lst_records():
    """List all DNS records"""
    response = requests.get(DREAMHOST_URL, params={
        'cmd': 'dns-list_records',
        'key': DREAMHOST_ACCESS_KEY,
    })
    if response.status_code != 200:
        raise RuntimeError("did not receive a response")

    df = pd.read_csv(StringIO(response.text.removeprefix("success\n")), sep='\t')
    df = df[df['editable']==1][['record','type','value']]

    summary = []
    for r in sorted(df['record'].unique()):
        for t in sorted(df[df['record']==r]['type'].unique()):
            summary.append({
                "dnsName" : r,
                "recordType" : t,
                "targets" : [v for v in sorted(df[(df['record']==r)&(df['type']==t)]['value'].unique())]
            })
    return json.dumps(summary)

def del_record(record_name, record_type, record_value):
    """Remove a record from the list"""
    response = requests.get(DREAMHOST_URL, params={
        'cmd': 'dns-remove_record',
        'key': DREAMHOST_ACCESS_KEY,
        'record': record_name,
        'type': record_type,
        'value': record_value
    })
    if response.status_code != 200:
        raise RuntimeError("did not receive a response")

def add_record(record_name, record_type, record_value):
    """Remove a record from the list"""
    response = requests.get(DREAMHOST_URL, params={
        'cmd': 'dns-add_record',
        'key': DREAMHOST_ACCESS_KEY,
        'record': record_name,
        'type': record_type,
        'value': record_value,
        'comment': 'modified dyanmically by external-dns',
    })
    if response.status_code != 200:
        raise RuntimeError("did not receive a response")

def upd_record(record_name, record_type, record_value):
    """Update a given record"""
    del_record(record_name, record_type, record_value)
    add_record(record_name, record_type, record_value)

# Negotiate        GET    /                   Negotiate DomainFilter
# Records          GET    /records            Get records
# AdjustEndpoints  POST   /adjustendpoints    Provider specific adjustments of records
# ApplyChanges     POST   /records            Apply record

@app.route("/", methods=["GET"])
def handle_negotiate():
    try:
        if request.method == 'GET':
            return lst_zones(), 200, {'Content-Type': CONTENT_TYPE}
    except Exception as e:
        pass
    return "Error listing zones", 500
    
@app.route("/records", methods=["GET", "POST"]) 
def handle_records():
    try:
        if request.method == 'GET':
            return lst_records(), 200, {'Content-Type': CONTENT_TYPE}
        if request.method == 'POST':
            data = json.loads(request.data)
            all_to_del = data.get('delete', []) + data.get('updateOld', [])
            for record in all_to_del:
                for target in record.targets:
                    del_record(
                        record_name=record.dnsName,
                        record_type=record.recordType,
                        record_value=record.target,
                    )
            all_to_add = data.get('create', []) + data.get('updateNew', [])
            for record in all_to_add:
                for target in record.targets:
                    add_record(
                        record_name=record.dnsName,
                        record_type=record.recordType,
                        record_value=record.target,
                    )
            return "Changes were accepted", 204
    except Exception as e:
        pass
    return "Error listing records", 500

@app.route('/adjustendpoints', methods=['POST'])
def handle_adjustendpoints():
    try:
        if request.method == 'POST':
            data = json.loads(request.data)
            for record in data:
                upd_record(
                    record_name=record.dnsName,
                    record_type=record.recordType,
                    record_value=record.target,
                )
            return lst_records(), 200, {'Content-Type': CONTENT_TYPE}    
    except Exception as e:
        pass
    return "Error adjusting endpoints", 500

if __name__ == '__main__':
    app.run(host='localhost', port=8888)

