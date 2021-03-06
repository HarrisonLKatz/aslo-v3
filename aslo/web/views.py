from . import web
from flask import (render_template,
                   abort, request, redirect,
                   url_for, flash, session, send_from_directory)
from flask import current_app as app
from aslo.persistence.activity import Activity
from aslo.service import activity as activity_service
from flask_babel import gettext
import os


@web.route('/', defaults={'page': 1})
@web.route('/page/<int:page>')
def index(page=1):
    # If Ignore_lang in the parameters, show all other non-translated apps
    lang_code = session['lang_code']
    ignore_lang = request.args.get('ignore_lang', False, type=bool)
    if ignore_lang:
        activities = activity_service.get_all(page=page)
    else:
        activities = activity_service.filter_by_lang_code(lang_code, page=page)

    return render_template('index.html', activities=activities,
                           lang_code=lang_code, ignore_lang=ignore_lang)


@web.route('/<bundle_id>/<activity_version>', strict_slashes=False)
def activity_detail(bundle_id, activity_version):
    lang_code = session['lang_code']
    activity_version = float(activity_version)
    activity = Activity.get_by_bundle_id(bundle_id)
    if activity is None:
        abort(404)

    release = activity_service.find_release(activity, activity_version)
    if release is None:
        abort(404)
    else:
        return render_template('detail.html', activity=activity,
                               current_release=release, lang_code=lang_code)


@web.route('/search', methods=['GET', 'POST'])
@web.route('/search/page/<int:page>', methods=['GET', 'POST'])
def search(page=1):
    if request.method == 'POST':
        name = request.form['name']
        category_option = request.form['category-option']
        category_option_query = request.form['category-option-query']
    else:
        name = request.args.get('name')
        category_option = request.args.get('category-option')
        category_option_query = request.args.get('category-option-query')

    if not name and not category_option:
        return redirect(url_for('web.index'))

    lang_code = session['lang_code']

    if not category_option_query or 'all' in category_option_query:
        category_option_query = None
    else:
        category_option_query = category_option_query.strip().lower()

    activities = activity_service.search_by_activity_name(
        lang_code=lang_code, activity_name=name,
        page=page, category_name=category_option_query)

    if name and not category_option_query:
        flash(gettext("Search Results for {}").format(name), 'success')
    elif name and category_option_query:
        flash(gettext("Search Results for {} and {} category").format(
            name, category_option), 'success')
    else:
        flash(gettext("Search Results for {} category").format(
            category_option), 'success')
    category_options = {'placeholder': category_option,
                        'actual_query': category_option_query
                        }
    return render_template('index.html', activities=activities,
                           search_query=name,
                           category_options=category_options,
                           lang_code=lang_code)


@web.route("/downloads/<bundle_id>/<bundle_name>")
def serve_bundle(bundle_id, bundle_name):
    bundle_location = os.path.join(app.config['BUILD_BUNDLE_DIR'], bundle_id)
    file_location = os.path.join(bundle_location, bundle_name)
    if os.path.exists(file_location):
        return send_from_directory(bundle_location, bundle_name)
    else:
        flash("{} doesn't exists".format(bundle_name), 'error')
        return redirect(url_for('web.index'))


@web.route('/categories/<category_name>')
@web.route('/categories/<category_name>/<int:page>')
def categories(category_name, page=1):
    lang_code = session['lang_code']
    if not category_name:
        return redirect(url_for('web.index'))
    activities = activity_service.search_by_category(
        category_name, lang_code=lang_code, page=page)
    return render_template('index.html', activities=activities,
                           lang_code=lang_code, category_query=category_name)
