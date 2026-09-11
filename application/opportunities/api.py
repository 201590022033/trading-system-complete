"""Thin Flask adapter for canonical read-only opportunity services."""
from flask import Blueprint,jsonify,request
from .service import serialize_opportunity,serialize_policy,serialize_risk

def error(code,message,status):return jsonify(error={'code':code,'message':message,'http_status':status}),status
def create_blueprint(service):
 bp=Blueprint('canonical_opportunities',__name__)
 @bp.get('/api/v1/opportunities')
 def listing():
  raw=request.args.get('limit');
  try: limit=int(raw) if raw is not None else None;items=service.list_opportunities(limit)
  except ValueError as exc:return error('INVALID_REQUEST',str(exc),422)
  return jsonify(opportunities=[serialize_opportunity(x) for x in items],count=len(items),score_semantics='comparative research score; not probability of profit')
 @bp.get('/api/v1/opportunities/<oid>')
 def detail(oid):
  try:return jsonify(opportunity=serialize_opportunity(service.get_opportunity(oid)))
  except KeyError:return error('OPPORTUNITY_NOT_FOUND','opportunity not found',404)
 @bp.get('/api/v1/opportunities/<oid>/policy')
 def policy(oid):
  try:return jsonify(policy=serialize_policy(service.get_policy(oid)))
  except KeyError:
   if oid not in service._opportunities:return error('OPPORTUNITY_NOT_FOUND','opportunity not found',404)
   return error('POLICY_UNAVAILABLE','required upstream policy unavailable',503)
 @bp.get('/api/v1/opportunities/<oid>/risk')
 def risk(oid):
  try:return jsonify(risk=serialize_risk(service.get_risk(oid)))
  except KeyError:
   if oid not in service._opportunities:return error('OPPORTUNITY_NOT_FOUND','opportunity not found',404)
   return error('RISK_UNAVAILABLE','required upstream risk evaluation unavailable',503)
 @bp.get('/api/v1/opportunities/<oid>/intent')
 def intent(oid):
  try:value=service.get_trade_intent_preview(oid)
  except KeyError:
   if oid not in service._opportunities:return error('OPPORTUNITY_NOT_FOUND','opportunity not found',404)
   return error('UPSTREAM_STATE_UNAVAILABLE','required upstream state unavailable',503)
  body={'intent':value.to_dict()}
  return (jsonify(body),200) if value.execution_readiness=='READY_FOR_PREVIEW' else (jsonify(**body,error={'code':'PREREQUISITE_UNRESOLVED','message':'trade intent prerequisites are unresolved','http_status':409}),409)
 return bp
