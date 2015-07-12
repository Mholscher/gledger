from ..GLedger import db 

class Account(db.Model)
    id = db.Column(db.Integer, Sequence('account_id_seq'),primary_key=True)
    name = db.Column(db.String(15), nullable=false)
    role = db.Column(db.string(1))