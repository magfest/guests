from guests import *


@all_renderable()
class Root:
    def index(self, session, id, message=''):
        guest = session.guest_group(id)

        def _deadline(item):
            return guest.deadline_from_model(item['name'])

        return {
            'message': message,
            'guest': guest,
            'sorted_checklist': sorted(filter(_deadline, c.CHECKLIST_ITEMS), key=_deadline)
        }

    def agreement(self, session, guest_id, message='', **params):
        guest = session.guest_group(guest_id)
        guest_info = session.guest_info(params, restricted=True)
        if cherrypy.request.method == 'POST':
            if not guest_info.performer_count:
                message = 'You must tell us how many people are in your group'
            elif not guest_info.poc_phone:
                message = 'You must enter an on-site point-of-contact cellphone number'
            elif not guest_info.arrival_time and not guest.group_type == c.GUEST:
                message = 'You must enter your expected arrival time'
            elif guest_info.bringing_vehicle and not guest_info.vehicle_info:
                message = 'You must provide your vehicle information'
            else:
                guest.info = guest_info
                session.add(guest_info)
                raise HTTPRedirect('index?id={}&message={}', guest.id, 'Your group information has been uploaded')

        return {
            'guest': guest,
            'guest_info': guest.info or guest_info,
            'message': message
        }

    def bio(self, session, guest_id, message='', bio_pic=None, **params):
        guest = session.guest_group(guest_id)
        guest_bio = session.guest_bio(params, restricted=True)
        if cherrypy.request.method == 'POST':
            if not guest_bio.desc:
                message = 'Please provide a brief bio for our website'

            if not message and bio_pic.filename:
                guest_bio.pic_filename = bio_pic.filename
                guest_bio.pic_content_type = bio_pic.content_type.value
                if guest_bio.pic_extension not in c.ALLOWED_BIO_PIC_EXTENSIONS:
                    message = 'Bio pic must be one of ' + ', '.join(c.ALLOWED_BIO_PIC_EXTENSIONS)
                else:
                    with open(guest_bio.pic_fpath, 'wb') as f:
                        shutil.copyfileobj(bio_pic.file, f)

            if not message:
                guest.bio = guest_bio
                session.add(guest_bio)
                raise HTTPRedirect('index?id={}&message={}', guest.id, 'Your bio information has been updated')

        return {
            'guest': guest,
            'guest_bio': guest.bio or guest_bio,
            'message': message
        }

    @cherrypy.expose(['w9'])
    def taxes(self, session, guest_id=None, message='', w9=None, **params):
        if not guest_id:
            guest_id = params.pop('id', None)
        assert guest_id, 'Either a guest_id or id is required'
        guest = session.guest_group(guest_id)
        guest_taxes = session.guest_taxes(params, restricted=True)
        if cherrypy.request.method == 'POST':
            guest_taxes.w9_filename = w9.filename
            guest_taxes.w9_content_type = w9.content_type.value
            if guest_taxes.w9_extension not in c.ALLOWED_W9_EXTENSIONS:
                message = 'Uploaded file type must be one of ' + ', '.join(c.ALLOWED_W9_EXTENSIONS)
            else:
                with open(guest_taxes.w9_fpath, 'wb') as f:
                    shutil.copyfileobj(w9.file, f)
                guest.taxes = guest_taxes
                session.add(guest_taxes)
                raise HTTPRedirect('index?id={}&message={}', guest.id, 'W9 uploaded')

        return {
            'guest': guest,
            'guest_taxes': guest.taxes or guest_taxes,
            'message': message
        }

    def stage_plot(self, session, guest_id, message='', plot=None, **params):
        guest = session.guest_group(guest_id)
        guest_stage_plot = session.guest_stage_plot(params, restricted=True)
        if cherrypy.request.method == 'POST':
            guest_stage_plot.filename = plot.filename
            guest_stage_plot.content_type = plot.content_type.value
            if guest_stage_plot.stage_plot_extension not in c.ALLOWED_STAGE_PLOT_EXTENSIONS:
                message = 'Uploaded file type must be one of ' + ', '.join(c.ALLOWED_STAGE_PLOT_EXTENSIONS)
            else:
                with open(guest_stage_plot.fpath, 'wb') as f:
                    shutil.copyfileobj(plot.file, f)
                guest.stage_plot = guest_stage_plot
                session.add(guest_stage_plot)
                raise HTTPRedirect('index?id={}&message={}', guest.id, 'Stage directions uploaded')

        return {
            'guest': guest,
            'guest_stage_plot': guest.stage_plot or guest_stage_plot,
            'message': message
        }

    def panel(self, session, guest_id, message='', **params):
        guest = session.guest_group(guest_id)
        guest_panel = session.guest_panel(params, checkgroups=['tech_needs'])
        if cherrypy.request.method == 'POST':
            if not guest_panel.wants_panel:
                message = 'You need to tell us whether you want to present a panel'
            elif guest_panel.wants_panel == c.NO_PANEL:
                guest_panel.name = guest_panel.length = guest_panel.desc = guest_panel.tech_needs = ''
            elif not guest_panel.name:
                message = 'Panel Name is a required field'
            elif not guest_panel.length:
                message = 'Panel Length is a required field'
            elif not guest_panel.desc:
                message = 'Panel Description is a required field'

            if not message:
                guest.panel = guest_panel
                session.add(guest_panel)
                raise HTTPRedirect('index?id={}&message={}', guest.id, 'Panel preferences updated')

        return {
            'guest': guest,
            'guest_panel': guest.panel or guest_panel,
            'message': message
        }

    def merch(self, session, guest_id, message='', coverage=False, warning=False, **params):
        guest = session.guest_group(guest_id)
        guest_merch = session.guest_merch(params, checkgroups=GuestMerch.all_checkgroups, bools=GuestMerch.all_bools)
        guest_merch.handlers = guest_merch.extract_handlers(params)
        group_params = dict()
        if cherrypy.request.method == 'POST':
            message = check(guest_merch)
            if not message:
                if c.REQUIRE_DEDICATED_GUEST_TABLE_PRESENCE and guest_merch.selling_merch == c.OWN_TABLE and \
                                guest.group_type == c.BAND and not all([coverage, warning]):
                    message = 'You cannot staff your own table without checking the boxes to agree to our conditions'
                elif guest.group_type == c.GUEST and guest_merch.selling_merch == c.OWN_TABLE:
                    for field_name in ['country', 'region', 'zip_code', 'address1', 'address2', 'city']:
                        group_params[field_name] = params.get(field_name, '')

                    if not guest.info and not guest_merch.tax_phone:
                        message = 'You must provide a phone number for tax purposes.'
                    elif not (params['country'] and params['region'] and params['zip_code'] and params['address1'] and
                                  params['city']):
                        message = 'You must provide an address for tax purposes.'
                    else:
                        guest.group.apply(group_params, restricted=True)
            if not message:
                guest.merch = guest_merch
                session.add(guest_merch)
                raise HTTPRedirect('index?id={}&message={}', guest.id, 'Your merchandise preferences have been saved')
        else:
            guest_merch = guest.merch

        return {
            'guest': guest,
            'guest_merch': guest_merch,
            'group': group_params or guest.group,
            'message': message
        }

    @ajax
    def save_inventory_item(self, session, guest_id, **params):
        guest = session.guest_group(guest_id)
        if guest.merch:
            guest_merch = guest.merch
        else:
            guest_merch = GuestMerch()
            guest.merch = guest_merch

        inventory = GuestMerch.extract_inventory(params)
        message = GuestMerch.validate_inventory(inventory)
        if not message:
            guest_merch.update_inventory(inventory)
            guest_merch.selling_merch = c.ROCK_ISLAND
            session.add(guest_merch)
            session.commit()

        return {'error': message}

    @ajax
    def remove_inventory_item(self, session, guest_id, item_id):
        guest = session.guest_group(guest_id)
        if guest.merch:
            guest_merch = guest.merch
        else:
            guest_merch = GuestMerch()
            guest.merch = guest_merch

        message = ''
        if not guest_merch.remove_inventory_item(item_id):
            message = 'Item not found'
        else:
            session.add(guest_merch)
            session.commit()
        return {'error': message}

    def charity(self, session, guest_id, message='', **params):
        guest = session.guest_group(guest_id)
        guest_charity = session.guest_charity(params)
        if cherrypy.request.method == 'POST':
            if not guest_charity.donating:
                message = 'You need to tell us whether you are donating anything'
            elif guest_charity.donating == c.DONATING and not guest_charity.desc:
                message = 'You need to tell us what you intend to donate'
            else:
                guest.charity = guest_charity
                session.add(guest_charity)
                raise HTTPRedirect('index?id={}&message={}', guest.id, 'Your charity decisions have been saved')

        return {
            'guest': guest,
            'guest_charity': guest.charity or guest_charity,
            'message': message
        }

    def autograph(self, session, guest_id, message='', **params):
        guest = session.guest_group(guest_id)
        guest_autograph = session.guest_autograph(params)
        if cherrypy.request.method == 'POST':
            guest_autograph.length = 60 * int(params['length'])  # Convert hours to minutes
            guest.autograph = guest_autograph
            session.add(guest_autograph)
            raise HTTPRedirect('index?id={}&message={}', guest.id, 'Your autograph sessions have been saved')

        return {
            'guest': guest,
            'guest_autograph': guest.autograph or guest_autograph,
            'message': message
        }

    def interview(self, session, guest_id, message='', **params):
        guest = session.guest_group(guest_id)
        guest_interview = session.guest_interview(params, bools=['will_interview', 'direct_contact'])
        if cherrypy.request.method == 'POST':
            if guest_interview.will_interview and not guest_interview.email:
                message = 'Please provide an email for interview requests.'
            else:
                guest.interview = guest_interview
                session.add(guest_interview)
                raise HTTPRedirect('index?id={}&message={}', guest.id, 'Your interview preferences have been saved')

        return {
            'guest': guest,
            'guest_interview': guest.interview or guest_interview,
            'message': message
        }

    def travel_plans(self, session, guest_id, message='', **params):
        guest = session.guest_group(guest_id)
        guest_travel_plans = session.guest_travel_plans(params, checkgroups=['modes'])
        if cherrypy.request.method == 'POST':
            if not guest_travel_plans.modes:
                message = 'Please tell us how you will arrive at MAGFest.'
            elif c.OTHER in guest_travel_plans.modes_ints and not guest_travel_plans.modes_text:
                message = 'You need to tell us what "other" travel modes you are using.'
            elif not guest_travel_plans.details:
                message = 'Please provide details of your arrival and departure plans.'
            else:
                guest.travel_plans = guest_travel_plans
                session.add(guest_travel_plans)
                raise HTTPRedirect('index?id={}&message={}', guest.id, 'Your travel plans have been saved')

        return {
            'guest': guest,
            'guest_travel_plans': guest.travel_plans or guest_travel_plans,
            'message': message
        }

    def view_inventory_file(self, session, id, item_id, name):
        guest_merch = session.guest_merch(id)
        if guest_merch:
            item = guest_merch.inventory.get(item_id)
            if item:
                filename = item.get('{}_filename'.format(name))
                download_filename = item.get('{}_download_filename'.format(name), filename)
                content_type = item.get('{}_content_type'.format(name))
                filepath = guest_merch.inventory_path(filename)
                if filename and download_filename and content_type and os.path.exists(filepath):
                    filesize = os.path.getsize(filepath)
                    cherrypy.response.headers['Accept-Ranges'] = 'bytes'
                    cherrypy.response.headers['Content-Length'] = filesize
                    cherrypy.response.headers['Content-Range'] = 'bytes 0-{}'.format(filesize)
                    return serve_file(filepath, disposition='inline', name=download_filename, content_type=content_type)
                else:
                    raise cherrypy.HTTPError(404, "File not found")

    def view_bio_pic(self, session, id):
        guest = session.guest_group(id)
        return serve_file(guest.bio.pic_fpath, disposition="attachment", name=guest.bio.download_filename, content_type=guest.bio.pic_content_type)

    def view_w9(self, session, id):
        guest = session.guest_group(id)
        return serve_file(guest.taxes.w9_fpath, disposition="attachment", name=guest.taxes.download_filename, content_type=guest.taxes.w9_content_type)

    def view_stage_plot(self, session, id):
        guest = session.guest_group(id)
        return serve_file(guest.stage_plot.fpath, disposition="attachment", name=guest.stage_plot.download_filename, content_type=guest.stage_plot.content_type)
