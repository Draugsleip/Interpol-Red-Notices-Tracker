import os
from flask import Flask, render_template, Response
from sqlalchemy import func

from Organizer.database_config import LocalSession,Notice
from Organizer.minio_client import MinioClient
import pycountry
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'Webapp/templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR,static_url_path='/static')
minio = MinioClient()

@app.route('/')
def homepage():
    session = LocalSession()
    try:
        total_notices = session.query(func.count(Notice.idx)).scalar()
        last_updated = session.query(func.max(Notice.upload_time)).scalar()
    finally:
        session.close()

    return render_template('homepage.html',
                           total_notices=total_notices,
                           last_updated=last_updated)

@app.route('/notice_list')
def notice_list():
    session = LocalSession()

    try:
        notices = session.query(Notice).order_by(Notice.upload_time.desc()).all()
        last_updated = session.query(func.max(Notice.upload_time)).scalar()
    finally:
        session.close()

    return render_template('notice_list.html', all_notices=notices, last_updated = last_updated)

@app.route('/notice/<path:entity_id>')
def notice_detail(entity_id):
    session = LocalSession()
    try:
        notice = session.query(Notice).filter(Notice.entity_id == entity_id).first()
        if not notice:
            return f"Notice {entity_id} not found"

        img_prefix = f"{entity_id}/"
        imgs = minio.list_from_minio(prefix=img_prefix)

        reference_link = session.query(Notice).filter(Notice.entity_id == entity_id).first().imgs_link
        reference_link = str(reference_link).removesuffix('/images')
    finally:
        session.close()


    return render_template('notice_detail.html',
                           notice=notice,
                           images=imgs,
                           source= reference_link,
                           last_updated = notice.upload_time)

# access imgs from minio
@app.route('/image/<path:object_name>')
def minio_get_img(object_name):
    img_bytes = minio.get_image(object_name)
    if img_bytes is None:
        return f"No image found for {object_name}"

    return Response(img_bytes, mimetype='image/png')

# lang id converter
@app.template_filter('language_names')
def language_names(language_ids):
    if not language_ids or language_ids is None:
        return "-"

    try:
        lan = pycountry.languages.get(alpha_3=language_ids.upper())

        if not lan:
            lan = pycountry.languages.get(alpha_2=language_ids.lower())

        return lan.name if lan else language_ids
    except:
        return language_ids

# coutnry id converter
@app.template_filter('country_names')
def country_names_filter(country_ids):
    if not country_ids or country_ids is None:
        return "-"

    if isinstance(country_ids, str):
        try:
            country = pycountry.countries.get(alpha_2=country_ids.upper().strip())
            return country.name if country else country_ids
        except:
            return country_ids

    country_names = []
    for country_id in country_ids:
        try:
            country = pycountry.countries.get(alpha_2=country_id)
            if country:
                country_names.append(country.name)
            else:
                country_names.append(country_id)
        except Exception as e:
            country_names.append(country_id)

    return country_names

# gender code converter
@app.template_filter('sex_id')
def gender(sex_id):
    if sex_id is None or not sex_id:
        return "-"

    sex_id_codes = {
        'M': 'Male',
        'F': 'Female',
        'U': 'Unknown'
    }
    if isinstance(sex_id, str):
        return sex_id_codes.get(sex_id.upper(), sex_id)
    if isinstance(sex_id, list):
        return [sex_id_codes.get(str(sex_idx).upper(), sex_idx) for sex_idx in sex_id]


# hair color code converter
@app.template_filter('hair_color')
def hair_color(color_id):
    if not color_id or color_id is None:
        return "-"

    color_codes = {
        'BLA': 'Black',
        'BRO': 'Brown',
        'BROL': 'Light Brown',
        'BROF': 'Fawn Brown',
        'RED': 'Red',
        'REDA': 'Auburn',
        'WHI': 'White',
        'GRY': 'Gray',
        'GRYG': 'Graphite Gray',
        'YELB': 'Blond',
        'YELBD': 'Dark Blond',
        'HAIB': 'Bald',
        'HAID': 'Dyed',
        'OTHD': 'Other (Dark)'
    }
    if isinstance(color_id, str):
        return color_codes.get(color_id.upper(), color_id)
    if isinstance(color_id, list):
        return [color_codes.get(str(color_idx).upper(), color_idx) for color_idx in color_id]

# eye color code converter
@app.template_filter('eye_color')
def eye_color(color_id):

    if not color_id or color_id is None:
        return "-"
    color_codes = {
        'BRO': 'Brown',
        'BROD': 'Dark Brown',
        'BROL': 'Light Brown',
        'BROH': 'Brown-Hazel',
        'BLU': 'Blue',
        'BLUL': 'Light Blue',
        'GRE': 'Green',
        'GRY': 'Gray',
        'BLA': 'Black',
        'OTHL': 'Other (Light)',
        'OTHD': 'Other (Dark)'
    }
    if isinstance(color_id, str):
        return color_codes.get(color_id.upper(), color_id)
    if isinstance(color_id, list):
        return [color_codes.get(str(color_idx).upper(), color_idx) for color_idx in color_id]

# for calculating notice age according to the current time
@app.context_processor
def get_now():
    return {'now': datetime.now()}

if __name__ == "__main__":
    app.run(debug=False)
