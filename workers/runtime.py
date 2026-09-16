"""Offline causal handlers; no implicit provider/network or broker invocation."""
from shadow_learning import ObservationRecord, ShadowDecision, OutcomeLabel
from shadow_learning_pipeline import production_shadow_decision, label_decision, aggregate_evidence

def runtime_handlers(repository):
    def observation(job):
        record=ObservationRecord(**job.checkpoint['observation'])
        repository.save_observation(record)
        return {'observation_id':record.observation_id}

    def decision(job):
        from operational_intelligence import service
        data=repository.get_observation(job.checkpoint['observation_id'])
        if data is None: raise ValueError('observation missing')
        record=ObservationRecord(**data)
        result=production_shadow_decision(service,record.instrument,horizon=record.horizon,
            observation=record,decided_at=record.observed_at,
            horizon_context=job.checkpoint.get('horizon_context',{}),
            previous_signal=job.checkpoint.get('previous_signal',0))
        repository.save_shadow_decision(result)
        return {'decision_id':result.decision_id}

    def outcome(job):
        data=repository.get_shadow_decision(job.checkpoint['decision_id'])
        if data is None: raise ValueError('decision missing')
        result=label_decision(ShadowDecision(**data),**job.checkpoint['prices'])
        repository.save_outcome(result)
        return {'outcome_id':result.outcome_id}

    def evidence(job):
        data=repository.get_outcome(job.checkpoint['outcome_id'])
        if data is None: raise ValueError('outcome missing')
        result=OutcomeLabel(**data)
        decision=repository.get_shadow_decision(result.decision_id)
        aggregate_evidence(repository,result,instrument=decision['instrument'],horizon=decision['horizon'])
        return {'outcome_id':result.outcome_id}

    return {'observation-generation':observation,'shadow-decision-generation':decision,
            'outcome-labelling':outcome,'adaptive-evidence-update':evidence}
