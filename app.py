from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)

app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

content_ip = db.Table('content_ip',
                    db.Column('content_id', db.Integer, db.ForeignKey('content.id', ondelete="cascade")),
                    db.Column('ip_id', db.Integer, db.ForeignKey('ip.id', ondelete="cascade"))
                    )

content_ipv6 = db.Table('content_ipv6',
                    db.Column('content_id', db.Integer, db.ForeignKey('content.id', ondelete="cascade")),
                    db.Column('ipv6_id', db.Integer, db.ForeignKey('ipv6.id', ondelete="cascade"))
                    )

content_ipsub = db.Table('content_ipsub',
                    db.Column('content_id', db.Integer, db.ForeignKey('content.id', ondelete="cascade")),
                    db.Column('ipsub_id', db.Integer, db.ForeignKey('ipSubnet.id', ondelete="cascade"))
                    )

class Content(db.Model):
    __tablename__ = 'content'

    id = db.Column(db.Integer(), primary_key=True)
    includeTime = db.Column(db.DateTime())
    entryType = db.Column(db.Integer(), nullable=False)
    blockType = db.Column(db.String(255), nullable=False)
    hash = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date())
    number = db.Column(db.String(255), nullable=False)
    org = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(), nullable=False)
    id_domain = db.Column(db.Integer(), db.ForeignKey('domain.id', ondelete="cascade"))
    ts = db.Column(db.String(255), default="None")
    ip_list = db.relationship('Ip',
        secondary=content_ip,
        primaryjoin=(content_ip.c.content_id == id),
        backref=db.backref('content', lazy='dynamic'),
        cascade="all, delete",
        passive_deletes=True
    )
    ipv6_list = db.relationship('Ipv6',
        secondary=content_ipv6,
        primaryjoin=(content_ipv6.c.content_id == id),
        backref=db.backref('content', lazy='dynamic'),
        cascade="all, delete",
        passive_deletes=True
    )
    ipsub_list = db.relationship('IpSubnet',
        secondary=content_ipsub,
        primaryjoin=(content_ipsub.c.content_id == id),
        backref=db.backref('content', lazy='dynamic'),
        cascade="all, delete",
        passive_deletes=True
    )

    def __init__(self, id, includeTime, entryType, hash, date, number, org, url='None', blockType='None', id_domain=None, ts='None'):
        self.id = id
        self.includeTime = includeTime
        self.entryType = entryType
        self.blockType = blockType
        self.hash = hash
        self.date = date
        self.number = number
        self.org = org
        self.url = url
        self.id_domain = id_domain
        self.ts = ts

    def __repr__(self):
        return f""


class Domain(db.Model):
    __tablename__ = 'domain'

    id = db.Column(db.Integer(), primary_key=True)
    domain = db.Column(db.String(255), nullable=False)
    ts = db.Column(db.String(255), default="None")

    def __init__(self, id, domain, ts="None"):
        self.id = id
        self.domain = domain
        self.ts = ts

    def __repr__(self):
        return f""


class Ip(db.Model):
    __tablename__ = 'ip'

    id = db.Column(db.Integer(), primary_key=True)
    ip = db.Column(db.String(255), nullable=False)
    ts = db.Column(db.String(255), default="None")

    def __init__(self, id, ip, ts="None"):
        self.id = id
        self.ip = ip
        self.ts = ts

    def __repr__(self):
        return f""


class Ipv6(db.Model):
    __tablename__ = 'ipv6'

    id = db.Column(db.Integer(), primary_key=True)
    ipv6 = db.Column(db.String(255), nullable=False)
    ts = db.Column(db.String(255), default="None")

    def __init__(self, id, ipv6, ts="None"):
        self.id = id
        self.ipv6 = ipv6
        self.ts = ts

    def __repr__(self):
        return f""


class IpSubnet(db.Model):
    __tablename__ = 'ipSubnet'

    id = db.Column(db.Integer(), primary_key=True)
    ipsub = db.Column(db.String(255), nullable=False)
    ts = db.Column(db.String(255), default="None")

    def __init__(self, id, ipsub, ts="None"):
        self.id = id
        self.ipsub = ipsub
        self.ts = ts

    def __repr__(self):
        return f""


class Temp(db.Model):
    __tablename__ = 'temp'

    id = db.Column(db.Integer(), primary_key=True)
    temp = db.Column(db.Float(), nullable=False)
    id_domain = db.Column(db.Integer(), db.ForeignKey('domain.id', ondelete="cascade"))
    dateTimeRequest = db.Column(db.DateTime())

    def __init__(self, id, temp, id_domain, dateTimeRequest):
        self.id = id
        self.temp = temp
        self.id_domain = id_domain
        self.dateTimeRequest = dateTimeRequest

    def __repr__(self):
        return f""


class Kurs(db.Model):
    __tablename__ = 'kurs'

    id = db.Column(db.Integer(), primary_key=True)
    kurs = db.Column(db.Float(), nullable=False)
    id_domain = db.Column(db.Integer(), db.ForeignKey('domain.id', ondelete="cascade"), nullable=False)
    dateTimeRequest = db.Column(db.DateTime())

    def __init__(self, id, kurs, id_domain, dateTimeRequest):
        self.id = id
        self.kurs = kurs
        self.id_domain = id_domain
        self.dateTimeRequest = dateTimeRequest

    def __repr__(self):
        return f""

@app.route('/', methods=['post', 'get'])
def index():
    dom = request.args.get('dom')
    hash = request.args.get('hash')
    if dom:
        result = Content.query.join(Domain, Content.id_domain == Domain.id).filter(Domain.domain.contains(dom)).all()
        res_k = Kurs.query.join(Domain, Kurs.id_domain == Domain.id).filter(Domain.domain.contains(dom)).all()
        res_t = Temp.query.join(Domain, Temp.id_domain == Domain.id).filter(Domain.domain.contains(dom)).all()
    elif hash:
        result = Content.query.join(Domain, Content.id_domain == Domain.id).filter(Content.hash.contains(hash)).all()
        res_k, res_t = [], []
    else:
        result, res_k, res_t = [], [], []

    return render_template('index.html', res_k=res_k, res_t=res_t, results=result)

if __name__ == "__main__":
    app.run(debug=True)