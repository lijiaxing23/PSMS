# -*- coding: utf-8 -*-
from main.has_permission import *
from flask import Blueprint, request, safe_join, Response, send_file, make_response

from main import db
from models import Offer, History, User, Customers, Country, TimePrice
import json
import os
import datetime, time
import xlrd
import tempfile
from sqlalchemy import desc

offers = Blueprint('offers', __name__)

@offers.route('/', methods=["GET","POST"])
def index():
    return render_template("index.html")

@offers.route('/api/getlogin',methods=["GET","POST"])
def getlogin():
    return render_template("token.html")

@offers.route('/api/customer_select', methods=['POST', 'GET'])
def customerSelect():
    if request.method == "POST":
        data = request.get_json(force=True)
        result = []
        customers = Customers.query.filter(Customers.company_name.ilike('%' + data["name"] + '%')).all()
        for i in customers:
            data = {
                "id": i.id,
                "text": i.company_name
            }
            result += [data]
        response = {
            "code": 200,
            "result": result
        }
        return json.dumps(response)


@offers.route('/api/country_select', methods=["POST", "GET"])
def countrySelect():
    if request.method == "POST":
        data = request.get_json(force=True)
        result = []
        if u'\u4e00' <= data["name"] <= u'\u9fff':
            countries = Country.query.filter(Country.chinese.ilike('%' + data["name"] + '%')).all()
        else:
            countries = Country.query.filter(Country.british.ilike('%' + data["name"] + '%')).all()
        for i in countries:
            data = {
                "id": i.shorthand,
                "text": i.chinese
            }
            result += [data]
        response = {
            "code": 200,
            "result": result,
            "message": "success"
        }
        return json.dumps(response)
    else:
        return json.dumps({"code": 500, "message": "The request type wrong!"})


@offers.route('/api/user_select', methods=["POST", "GET"])
def userSelect():
    users = User.query.filter().all()
    result = []
    for i in users:
        data = {
            "id": i.id,
            "name": i.name,
            "email": i.email
        }
        result += [data]
    response = {
        "code": 200,
        "result": result,
        "message": "success"
    }
    return json.dumps(response)


@offers.route('/api/create_offer', methods=['POST', 'GET'])
def createOffer():
    if request.method == "POST":
        data = request.get_json(force=True)
        createdTime = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        updateTime = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        email_time = "2016-12-19 " + data["email_time"] + ":00"
        emailTime = float(time.mktime(time.strptime(email_time, '%Y-%m-%d %H:%M:%S')))

        offer = Offer(int(data["user_id"]), int(data["customer_id"]), data["status"], data["contract_type"],
                      data["contract_num"], float(data["contract_scale"]), data["os"], data["package_name"],
                      data["app_name"], data["app_type"].encode('utf-8'), data["preview_link"], data["track_link"],
                      data["material"], data["startTime"], data["endTime"], str(data["platform"]), str(data["country"]),
                      float(data["price"]), float(data["daily_budget"]), data["daily_type"],
                      float(data["total_budget"]), data["total_type"], data["distribution"], data["authorized"],
                      data["named_rule"], data["KPI"].encode('utf-8'), data["settlement"].encode('utf-8'),
                      data["period"].encode('utf-8'), data["remark"].encode('utf-8'), emailTime,
                      str(data["email_users"]), int(data["email_tempalte"]), createdTime, updateTime)
        try:
            db.session.add(offer)
            db.session.commit()
            db.create_all()

            for i in data['country_detail']:
                history = History(offer.id, int(data["user_id"]), "default", createdTime, status=data["status"],
                                  country=i["country"], country_price=i["price"], price=data["price"],
                                  daily_budget=float(data["daily_budget"]), daily_type=data["daily_type"],
                                  total_budget=float(data["total_budget"]), total_type=data["total_type"],
                                  KPI=data["KPI"], contract_type=data["contract_type"],
                                  contract_scale=float(data["contract_scale"]))
                db.session.add(history)
                db.session.commit()
                db.create_all()
            return json.dumps({"code": 200, "message": "success"})
        except Exception as e:
            print e
            return json.dumps({"code": 500, "message": "fail"})


@offers.route('/api/offer_show', methods=["POST", "GET"])
def offerShow():
    offers = Offer.query.all()
    result = []
    for i in offers:
        customerId = i.customer_id
        customer = Customers.query.filter_by(id=customerId).first()
        customerName = customer.company_name  # 客户名称
        status = i.status
        contract_type = i.contract_type
        os = i.os
        app_name = i.app_name
        data = {
            "offer_id": i.id,
            "status": status,
            "contract_type": contract_type,
            "os": os,
            "customer_id": customerName,
            "app_name": app_name,
            "startTime": i.startTime,
            "endTime": i.endTime,
            "country": str(i.country),
            "price": i.price,
            "updateTime": i.updateTime
        }
        result += [data]
    response = {
        "code": 200,
        "result": result,
        "message": "success"
    }
    return json.dumps(response)


@offers.route('/api/offer_detail/<id>', methods=["GET"])
@Permission.check(models=['offer_query'])
def offerDetail(id):
    offer = Offer.query.filter_by(id=int(id)).first()
    customerId = offer.customer_id
    customer = Customers.query.filter_by(id=customerId).first()
    userId = offer.user_id
    user = User.query.filter_by(id=userId).first()
    contract_type = offer.contract_type
    if contract_type != "cpa":
        contract_scale = 0
    else:
        contract_scale = offer.contract_scale
    plate = offer.platform
    emailTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(offer.email_time))[11:16]
    result = {
        "customer_id": customer.company_name,
        "status": offer.status,
        "contract_scale": contract_scale,
        "contract_num": offer.contract_num,
        "contract_type": offer.contract_type,
        "user_id": user.id,
        "os": offer.os,
        "package_name": offer.package_name,
        "app_name": offer.app_name,
        "app_type": offer.app_type,
        "preview_link": offer.preview_link,
        "track_link": offer.track_link,
        "material": offer.material,
        "startTime": offer.startTime,
        "endTime": offer.endTime,
        "platform": str(plate),
        "country": str(offer.country),
        "price": offer.price,
        "daily_budget": offer.daily_budget,
        "daily_type": offer.daily_type,
        "total_budget": offer.total_budget,
        "total_type": offer.total_type,
        "distribution": offer.distribution,
        "authorized": offer.authorized,
        "named_rule": offer.named_rule,
        "KPI": offer.KPI,
        "settlement": offer.settlement,
        "period": offer.period,
        "remark": offer.remark,
        "email_time": emailTime,
        "email_users": offer.email_users,
        "email_tempalte": offer.email_tempalte
    }
    historties = History.query.filter(History.offer_id == id, History.country != "").all()
    countries = []
    for i in historties:
        country = i.country
        countries.append(country)
    countries = list(set(countries))
    country_detail = []
    for i in countries:
        historty = History.query.filter(History.offer_id == id, History.country == i).order_by(
            desc(History.createdTime)).first()
        country = historty.country
        country_price = historty.country_price
        detail = {
            "country": country,
            "price": country_price
        }
        country_detail += [detail]
    result["country_detail"] = country_detail
    response = {
        "code": 200,
        "result": result,
        "message": "success"
    }
    return json.dumps(response)


@offers.route('/api/update_offer', methods=["POST", "GET"])
def updateOffer():
    if request.method == "POST":
        data = request.get_json(force=True)
        offer = Offer.query.filter_by(id=int(data["offer_id"])).first()
        flag = data["flag"]
        if offer is not None:
            try:
                offer.updateTime = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                offer.status = data["status"] if data["status"] != "" else offer.status
                offer.contract_type = data["contract_type"] if data["contract_type"] != "" else offer.contract_type
                offer.contract_scale = float(data["contract_scale"]) if data[
                                                                            "contract_scale"] != "" else offer.contract_scale
                offer.contract_num = data["contract_num"] if data["contract_num"] != "" else offer.contract_num
                offer.os = data["os"] if data["os"] != "" else offer.os
                offer.package_name = data["package_name"] if data["package_name"] != "" else offer.package_name
                offer.app_name = data["app_name"] if data["app_name"] != "" else offer.app_name
                offer.app_type = data["app_type"] if data["app_type"] != "" else offer.app_type
                offer.preview_link = data["preview_link"] if data["preview_link"] != "" else offer.preview_link
                offer.track_link = data["track_link"] if data["track_link"] != "" else offer.track_link
                offer.material = data["material"] if data["material"] != "" else offer.material
                offer.startTime = data["startTime"] if data["startTime"] != "" else offer.startTime
                offer.endTime = data["endTime"] if data["endTime"] != "" else offer.endTime
                offer.platform = str(data["platform"]) if str(data["platform"]) != "" else offer.platform
                offer.country = str(data["country"]) if str(data["country"]) != "" else offer.country
                offer.price = float(data["price"]) if data["price"] != "" else offer.price
                offer.daily_budget = float(data["daily_budget"]) if data["daily_budget"] != "" else offer.daily_budget
                offer.daily_type = data["daily_type"] if data["daily_type"] != "" else offer.daily_type
                offer.total_budget = float(data["total_budget"]) if data["total_budget"] != "" else offer.total_budget
                offer.total_type = data["total_type"] if data["total_type"] != "" else offer.total_type
                offer.distribution = data["distribution"] if data["distribution"] != "" else offer.distribution
                offer.authorized = data["authorized"] if data['authorized'] != "" else offer.authorized
                offer.named_rule = data["named_rule"] if data["named_rule"] != "" else offer.named_rule
                offer.KPI = data["KPI"].encode('utf-8') if data["KPI"] != "" else offer.KPI
                offer.settlement = data['settlement'].encode('utf-8') if data["settlement"] != "" else offer.settlement
                offer.period = data["period"].encode("utf-8") if data["period"] != "" else offer.period
                offer.remark = data["remark"].encode("utf-8") if data["remark"] != "" else offer.remark
                if data["email_time"] != "":
                    email_time = "2016-12-19 " + data["email_time"] + ":00"
                    emailTime = float(time.mktime(time.strptime(email_time, '%Y-%m-%d %H:%M:%S')))
                    offer.email_time = emailTime
                offer.email_users = str(data["email_users"]) if str(data["email_users"]) != "" else offer.email_users
                offer.email_tempalte = data["email_tempalte"] if data["email_tempalte"] != "" else offer.email_tempalte
                db.session.add(offer)
                db.session.commit()
                if "country_detail" in flag:
                    for i in data['country_detail']:
                        history = History(offer.id, offer.user_id, "update",
                                          (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime(
                                              "%Y-%m-%d %H:%M:%S"), country=i["country"], country_price=i["price"],
                                          price=float(data["price"]) if data["price"] != "" else 0,
                                          status=data["status"],
                                          daily_budget=float(data["daily_budget"]) if data["daily_budget"] != "" else 0,
                                          daily_type=data["daily_type"],
                                          total_budget=float(data["total_budget"]) if data['total_budget'] != "" else 0,
                                          total_type=data["total_type"], KPI=data["KPI"],
                                          contract_type=data["contract_type"],
                                          contract_scale=float(data["contract_scale"]))
                        db.session.add(history)
                        db.session.commit()
                        db.create_all()
                else:
                    history = History(offer.id, offer.user_id, "update",
                                      (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime(
                                          "%Y-%m-%d %H:%M:%S"),
                                      price=float(data["price"]) if data["price"] != "" else 0, status=data["status"],
                                      daily_budget=float(data["daily_budget"]) if data["daily_budget"] != "" else 0,
                                      daily_type=data["daily_type"],
                                      total_budget=float(data["total_budget"]) if data['total_budget'] != "" else 0,
                                      total_type=data["total_type"], KPI=data["KPI"],
                                      contract_type=data["contract_type"],
                                      contract_scale=float(data["contract_scale"]) if data[
                                                                                          "contract_scale"] != "" else 0)
                    db.session.add(history)
                    db.session.commit()
                    db.create_all()

                return json.dumps({"code": 200, "message": "success"})
            except Exception as e:
                print e
                return json.dumps({"code": 500, "message": "fail"})
        else:
            return json.dumps({"code": 400, "message": "offer is None"})


@offers.route("/api/history", methods=["POST", "GET"])
def historty():
    if request.method == "POST":
        data = request.get_json(force=True)
        offer_id = int(data["offer_id"])
        flag = data["flag"]
        if flag == "country_detail":
            country = []
            result = []
            history = History.query.filter(History.offer_id == offer_id, History.country != "")
            for i in history:
                country.append(i.country)
            country = list(set(country))
            print country
            for i in country:
                detail = []
                history_country = History.query.filter(History.offer_id == offer_id, History.country == i)
                for j in history_country:
                    createdTime = j.createdTime
                    country_price = j.country_price
                    country_data = {
                        "country_price": country_price,
                        "createdTime": createdTime
                    }
                    detail += [country_data]
                result += [{"country": i, "detail": detail}]
            response = {
                "code": 200,
                "result": result
            }
            return json.dumps(response)
        else:
            result = []
            if flag == "status":
                history = History.query.filter(History.offer_id == offer_id, History.status != "")
                for i in history:
                    status = i.status
                    createdTime = i.createdTime
                    user_id = i.user_id
                    user = User.query.filter(User.id == user_id).first()
                    detail = {
                        "username": user.name,
                        "status": status,
                        "createdTime": createdTime
                    }
                    result += [detail]
            elif flag == "contract_type":
                history = History.query.filter(History.offer_id == offer_id, History.contract_type != "")
                for i in history:
                    contract_type = i.contract_type
                    contract_scale = i.contract_scale
                    createdTime = i.createdTime
                    user_id = i.user_id
                    user = User.query.filter(User.id == user_id).first()
                    detail = {
                        "username": user.name,
                        "contract_type": contract_type,
                        "contract_scale": contract_scale,
                        "createdTime": createdTime
                    }
                    result += [detail]

            elif flag == "price":
                history = History.query.filter(History.offer_id == offer_id, History.price != "")
                for i in history:
                    price = i.price
                    createdTime = i.createdTime
                    user_id = i.user_id
                    user = User.query.filter(User.id == user_id).first()
                    detail = {
                        "username": user.name,
                        "price": price,
                        "createdTime": createdTime
                    }
                    result += [detail]
            elif flag == "daily_budget":
                history = History.query.filter(History.offer_id == offer_id, History.daily_budget != "")
                for i in history:
                    daily_budget = i.daily_budget
                    daily_type = i.daily_type
                    createdTime = i.createdTime
                    user_id = i.user_id
                    user = User.query.filter(User.id == user_id).first()
                    detail = {
                        "username": user.name,
                        "daily_budget": daily_budget,
                        "daily_type": daily_type,
                        "createdTime": createdTime
                    }
                    result += [detail]
            elif flag == "total_budget":
                history = History.query.filter(History.offer_id == offer_id, History.total_budget != "")
                for i in history:
                    total_budget = i.total_budget
                    total_type = i.total_type
                    createdTime = i.createdTime
                    user_id = i.user_id
                    user = User.query.filter(User.id == user_id).first()
                    detail = {
                        "username": user.name,
                        "total_budget": total_budget,
                        "total_type": total_type,
                        "createdTime": createdTime
                    }
                    result += [detail]
            elif flag == "KPI":
                history = History.query.filter(History.offer_id == offer_id, History.total_budget != "")
                for i in history:
                    KPI = i.KPI
                    createdTime = i.createdTime
                    user_id = i.user_id
                    user = User.query.filter(User.id == user_id).first()
                    detail = {
                        "username": user.name,
                        "KPI": KPI,
                        "createdTime": createdTime
                    }
                    result += [detail]
                    print
            f = lambda x, y: x if y in x else x + [y]
            response = {
                "code": 200,
                "result": reduce(f, [[], ] + result)
            }
            return json.dumps(response)


# 导入国家表
@offers.route("/api/country")
def country():
    wb = xlrd.open_workbook("/Users/liyin/Downloads/1.xlsx")

    wb.sheet_names()
    sh = wb.sheet_by_name(u'Sheet1')
    count = 0
    for rownum in range(sh.nrows):
        country = Country(sh.row_values(rownum)[0], sh.row_values(rownum)[1], sh.row_values(rownum)[2])
        db.session.add(country)
        db.session.commit()
        db.create_all()
        count += 1

    print count


# 导入国家对应的时间
@offers.route("/api/country_time", methods=["POST", "GET"])
def importCountry():
    if request.method == "POST":
        basedir = os.path.abspath(os.path.dirname(__file__))
        file_dir = os.path.join(basedir, 'upload')
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        unix_time = int(time.time())
        f = request.files['file']
        new_filename = str(unix_time) + '.xlsx'  # 修改了上传的文件名
        f.save(os.path.join(file_dir, new_filename))  # 保存文件到upload目录
        try:
            data = xlrd.open_workbook(file_dir + "/" + new_filename)
        except Exception, e:
            print e
        table = data.sheets()[0]

        nrows = table.nrows
        ncols = table.ncols
        data = []
        for rownum in range(1, nrows):
            date = []
            timea = []
            for col in range(1, ncols):
                timea.append(xlrd.xldate.xldate_as_datetime(table.row_values(0)[col], 1).strftime("%Y-%m-%d"))
                date.append(table.row_values(rownum)[col])
            result = {
                "country": table.row_values(rownum)[0],
                "date": date,
                "time": timea
            }
            data += [result]

        for i in data:
            for j in range(len(i["time"])):
                time_coun = i["time"][j]
                price = '%0.2f' % (i["date"][j])
                country = i['country']
                coun = Country.query.filter_by(shorthand=country).first()
                timePrice = TimePrice(coun.id, time_coun, price)
                db.session.add(timePrice)
                db.session.commit()
                db.create_all()

        response = {
            "code": 200,
            "data": data,
            "message": "success"
        }
    else:
        response = {
            "code": 500,
            "message": "fail"
        }
    return json.dumps(response)


@offers.route("/api/country_time_show", methods=["POST", "GET"])
def showCountryTime():
    if request.method == "POST":
        data = request.get_json(force=True)
        date = data['date']
        country = data["country"]
        countries = Country.query.filter_by(shorthand=country).first()
        countryId = countries.id
        month = date.split("-", 1)[1]
        year = int(date.split('-', 1)[0])
        if month in ["01", "03", "05", "07", "08", "10", "12"]:
            dateList = [date + "-01", date + "-02", date + "-03", date + "-04", date + "-05", date + "-06",
                        date + "-07", date + "-08", date + "-09", date + "-10", date + "-11", date + "-12",
                        date + "-13", date + "-14", date + "-15", date + "-16", date + "-17", date + "-18",
                        date + "-19", date + "-20", date + "-21", date + "-22", date + "-23", date + "-24",
                        date + "-25", date + "-26", date + "-27", date + "-28", date + "-29", date + "-30",
                        date + "-31"]
        elif month in ["04", "06", "09", "11"]:
            dateList = [date + "-01", date + "-02", date + "-03", date + "-04", date + "-05", date + "-06",
                        date + "-07", date + "-08", date + "-09", date + "-10", date + "-11", date + "-12",
                        date + "-13", date + "-14", date + "-15", date + "-16", date + "-17", date + "-18",
                        date + "-19", date + "-20", date + "-21", date + "-22", date + "-23", date + "-24",
                        date + "-25", date + "-26", date + "-27", date + "-28", date + "-29", date + "-30"]
        else:
            if year % 100 == 0 and year % 400 == 0:
                dateList = [date + "-01", date + "-02", date + "-03", date + "-04", date + "-05", date + "-06",
                            date + "-07", date + "-08",
                            date + "-09", date + "-10", date + "-11", date + "-12", date + "-13", date + "-14",
                            date + "-15", date + "-16",
                            date + "-17", date + "-18", date + "-19", date + "-20", date + "-21", date + "-22",
                            date + "-23", date + "-24",
                            date + "-25", date + "-26", date + "-27", date + "-28", date + "-29"]
            elif year % 100 != 0 and year % 4 == 0:
                dateList = [date + "-01", date + "-02", date + "-03", date + "-04", date + "-05", date + "-06",
                            date + "-07", date + "-08",
                            date + "-09", date + "-10", date + "-11", date + "-12", date + "-13", date + "-14",
                            date + "-15", date + "-16",
                            date + "-17", date + "-18", date + "-19", date + "-20", date + "-21", date + "-22",
                            date + "-23", date + "-24",
                            date + "-25", date + "-26", date + "-27", date + "-28", date + "-29"]
            else:
                dateList = [date + "-01", date + "-02", date + "-03", date + "-04", date + "-05", date + "-06",
                            date + "-07", date + "-08",
                            date + "-09", date + "-10", date + "-11", date + "-12", date + "-13", date + "-14",
                            date + "-15", date + "-16",
                            date + "-17", date + "-18", date + "-19", date + "-20", date + "-21", date + "-22",
                            date + "-23", date + "-24",
                            date + "-25", date + "-26", date + "-27", date + "-28"]
        result = []
        dateCurrent = []
        timePrices = TimePrice.query.filter(TimePrice.country_id == countryId).all()
        for t in timePrices:
            dateCurrent.append(t.date)
        for i in dateList:
            if i in dateCurrent:
                timePrice = TimePrice.query.filter_by(country_id=countryId, date=i).first()
                detail = {
                    "date": i,
                    "price": timePrice.price
                }
            else:
                detail = {
                    "date": i,
                    "price": ""
                }
            result += [detail]
        response = {
            "code": 200,
            "result": result,
            "message": "success"
        }
        return json.dumps(response)


@offers.route('/api/country_time_update', methods=["POST", "GET"])
def updateContryTime():
    data = request.get_json(force=True)
    result = data["result"]
    countryName = data["country"]
    country = Country.query.filter_by(shorthand=countryName).first()
    countryId = country.id
    for i in result:
        if i["price"] != "":
            timePrice = TimePrice.query.filter_by(country_id=countryId, date=i["date"]).first()
            if timePrice:
                timePrice.price = i["price"]
                try:
                    db.session.add(timePrice)
                    db.session.commit()
                except Exception as e:
                    print e
                    return json.dumps({"code": 500, "message": "fail"})
            else:
                timePriceNew = TimePrice(countryId, i["date"], i["price"])
                try:
                    db.session.add(timePriceNew)
                    db.session.commit()
                    db.create_all()
                except Exception as e:
                    print e
                    return json.dumps({"code": 500, "message": "fail"})
        else:
            pass
    return json.dumps({"code": 200, "message": "success"})


@offers.route('/static/<path:filename>')
def static_file_for_console(filename):
    filename = safe_join("../static", filename)
    if not os.path.isabs(filename):
        filename = os.path.join(offers.root_path, filename)
    if not os.path.isfile(filename):
        return Response(), 404
    return send_file(filename, conditional=True)


@offers.route('/<path>')
def today(path):
    base_dir = os.path.dirname(__file__)
    resp = make_response(open(os.path.join(base_dir, path)))
    resp.headers["Content-type"] = "application/json;charset=UTF-8"
    return resp
