import xml.etree.ElementTree as ET
from pycbrf.toolbox import ExchangeRates
import time
import requests
from flask import Flask
from config import Config
from flask_migrate import Migrate
from datetime import datetime
from psycopg2 import Error
import logging
import psycopg2
from psycopg2.extras import LoggingConnection
from app import db, Content, Ip, Ipv6, IpSubnet, content_ip, content_ipv6, content_ipsub, Domain, Kurs, Temp

par = Flask(__name__)

par.config.from_object(Config)
migrate = Migrate(par, db)

def kurs(date):
    rates = ExchangeRates(date)
    rates.date_requested
    rates.date_received
    rates.dates_match
    return rates[Config.code].value

def weather():
    Final_url = Config.base_url + "&units=metric" + "&appid=" + Config.api_key + "&q=" + Config.city
    weather_data = requests.get(Final_url).json()
    return weather_data['main']['temp']

def placeholder(id, buffer, value, value_id, counter, Model):
    cont = {}
    if subelem.text not in buffer.values():
        id[0] += 1
        buffer.setdefault(id[0], subelem.text)
        dict = {'id': id[0], value: subelem.text}
        if 'ts' in subelem.attrib:
            dict.setdefault('ts', subelem.attrib['ts'])
        cont = {'content_id': elem.attrib["id"], value_id: id[0]}
        db.session.add(Model(**dict))
        db.session.commit()
    else:
        for k, v in buffer.items():
            if v == subelem.text:
                cont = {'content_id': elem.attrib["id"], value_id: k}
    counter.append(cont)
    return id[0], buffer, counter

def executor(counter, content):
    for elem in counter:
        if (len(elem) != 0):
            db.session.execute(content.insert().values(**elem))
            db.session.commit()
    return counter, content


def create_proc(query):
    try:
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger("loggerinformation")

        # Подключиться к существующей базе данных
        connection = psycopg2.connect(connection_factory=LoggingConnection,
                                      user=Config.user,
                                      password=Config.password,
                                      host=Config.host,
                                      port=Config.port,
                                      database=Config.database)

        connection.initialize(logger)
        cursor = connection.cursor()
        cursor.execute(query)
        connection.commit()

    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")


postgresql_del = """
CREATE OR REPLACE PROCEDURE run_code() 
LANGUAGE plpgsql AS 
$body$
BEGIN
    DROP VIEW IF EXISTS my_view CASCADE;
	DROP FUNCTION IF EXISTS add_log() CASCADE;
	DROP TRIGGER IF EXISTS add_log ON public.content;
END
$body$;

CALL run_code();
"""

postgresql_code = """
CREATE OR REPLACE PROCEDURE run_code() 
LANGUAGE plpgsql AS 
$body$
BEGIN
    CREATE OR REPLACE VIEW my_view AS
        select d.domain, k.kurs, t.temp
	    FROM Domain d
	    INNER JOIN Kurs k ON (k.id_domain = d.id)
	    INNER JOIN Temp t ON (t.id_domain = d.id);

    CREATE TABLE IF NOT EXISTS book_audit_log (
        id bigint NOT NULL,
	    old_row_data jsonb,
        dateTimeDelite timestamp,
        PRIMARY KEY (id)
    );

    CREATE OR REPLACE FUNCTION add_log()
        RETURNS trigger AS
    $$
    begin
        if (TG_OP = 'DELETE') then
            INSERT INTO book_audit_log (
                id,
			    old_row_data,
    		    dateTimeDelite
            )
            VALUES(
                OLD.id,
                to_jsonb(OLD),
                NOW()
            );
            RETURN OLD;
        end if;
    end;
    $$
    LANGUAGE 'plpgsql';

    CREATE TRIGGER add_log
        BEFORE DELETE ON public.content 
        FOR EACH ROW EXECUTE PROCEDURE add_log();

END
$body$;

CALL run_code();
"""

create_proc(postgresql_del)
db.drop_all()

db.create_all()
create_proc(postgresql_code)

start_time = time.time()

tree = ET.parse('dump.xml')
root = tree.getroot()


ip_buffer, ipv6_buffer, ipsub_buffer, domains_buffer = {}, {}, {}, {}
id_ip, id_ipv6, id_ipsub, id_domain = [0], [0], [0], [0]


for elem in root:
    content = {}
    counter_ip, counter_ipv6, counter_ipsub = [], [], []
    ts = "None"
    try:
        for key in elem.attrib:
            if key == "hash":
                hash_int = int(elem.attrib[key].lower(), 16)
                content.setdefault(key, hash_int)
            elif key == "ts":
                ts = elem.attrib[key]
            else:
                content.setdefault(key, elem.attrib[key])
        for subelem in elem:
            if subelem.text == None:
                for key in subelem.attrib:
                    content.setdefault(key, subelem.attrib[key])
            else:
                if subelem.tag == "domain":
                    domains, temp_tab, kurs_tab = {}, {}, {}
                    if subelem.text not in domains_buffer.values():
                        id_domain[0] += 1
                        domains_buffer.setdefault(id_domain[0], subelem.text)
                        domains.setdefault('id', id_domain[0])
                        domains.setdefault('domain', subelem.text)
                        if 'ts' in subelem.attrib:
                            domains.setdefault('ts', subelem.attrib['ts'])
                        content.setdefault('id_domain', id_domain[0])

                        kurs_tab = {'id': id_domain[0], 'id_domain': id_domain[0], 'kurs': kurs(elem.attrib["includeTime"].split("T")[0]), 'dateTimeRequest': datetime.now()}

                        temp_tab = {'id': id_domain[0], 'id_domain': id_domain[0], 'temp': weather(), 'dateTimeRequest': datetime.now()}

                        db.session.add(Domain(**domains))
                        db.session.add(Kurs(**kurs_tab))
                        db.session.add(Temp(**temp_tab))
                        db.session.commit()
                    else:
                        for k, v in domains_buffer.items():
                            if v == subelem.text:
                                content.setdefault('id_domain', k)
                elif subelem.tag == "ip":
                    placeholder(id_ip, ip_buffer, 'ip', 'ip_id', counter_ip, Ip)
                elif subelem.tag == "ipv6":
                    placeholder(id_ipv6, ipv6_buffer, 'ipv6', 'ipv6_id', counter_ipv6, Ipv6)
                elif subelem.tag == "ipSubnet":
                    placeholder(id_ipsub, ipsub_buffer, 'ipsub', 'ipsub_id', counter_ipsub, IpSubnet)
                else:
                    content.setdefault(subelem.tag, subelem.text)
        content.setdefault('ts', ts)

        db.session.add(Content(**content))
        db.session.commit()

        executor(counter_ip, content_ip)
        executor(counter_ipv6, content_ipv6)
        executor(counter_ipsub, content_ipsub)
    except requests.exceptions.ReadTimeout:
        print("\n Переподключение к серверам \n")
        time.sleep(3)


print("Время обработки: %s секунд" % (time.time() - start_time))