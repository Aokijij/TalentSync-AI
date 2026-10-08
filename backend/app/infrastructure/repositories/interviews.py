from app.infrastructure.database.models import (
    InterviewParticipant,
    InterviewRoom,
    InterviewSignal,
)


class InterviewRepository:
    def __init__(self, session):
        self.session = session

    def get(self, room_id):
        return self.session.get(InterviewRoom, room_id)

    def for_application(self, application_id):
        return self.session.query(InterviewRoom).filter_by(application_id=application_id).first()

    def rooms(self):
        return self.session.query(InterviewRoom).order_by(InterviewRoom.created_at.desc()).limit(500).all()

    def new_room(self, **values):
        return InterviewRoom(**values)

    def participants(self, room_id):
        return self.session.query(InterviewParticipant).filter_by(room_id=room_id).all()

    def participant(self, participant_id):
        return self.session.get(InterviewParticipant, participant_id)

    def new_participant(self, **values):
        return InterviewParticipant(**values)

    def new_signal(self, **values):
        return InterviewSignal(**values)

    def signals(self, room_id, participant_id, after_id, now):
        return self.session.query(InterviewSignal).filter(InterviewSignal.room_id == room_id,
            InterviewSignal.recipient_id == participant_id, InterviewSignal.id > after_id,
            InterviewSignal.expires_at > now).order_by(InterviewSignal.id).limit(100).all()

    def cleanup(self, now, room_id=None):
        for model in [InterviewSignal, InterviewParticipant]:
            query = self.session.query(model)
            if room_id is None:
                query = query.filter(model.expires_at <= now)
            else:
                query = query.filter(model.room_id == room_id)
            query.delete(synchronize_session="fetch")
