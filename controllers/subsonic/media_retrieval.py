# -*- coding: utf-8 -*-

import imghdr
import logging
import os
import StringIO

from lxml import etree
from werkzeug.wrappers import Response
from werkzeug.wsgi import wrap_file

from odoo import http
from odoo.http import request
from common import SubsonicREST

_logger = logging.getLogger(__name__)


class MusicSubsonicMediaRetrieval(http.Controller):
    @http.route(['/rest/stream.view'], type='http', auth='public', csrf=False, methods=['GET', 'POST'])
    def stream(self, **kwargs):
        rest = SubsonicREST(kwargs)
        success, response = rest.check_login()
        if not success:
            return response

        trackId = kwargs.get('id')
        if trackId:
            track = request.env['oomusic.track'].browse([int(trackId)])
            if not track.exists():
                return rest.make_error(code='70', message='Song not found')
        else:
            return rest.make_error(code='10', message='Required int parameter "id" is not present')

        maxBitRate = int(kwargs.get('maxBitRate', 0))
        output_format = kwargs.get('format', 'mp3')
        estimateContentLength = kwargs.get('estimateContentLength', False)

        # Only for video
        # timeOffset = kwargs.get('timeOffset')
        # size = kwargs.get('size')
        # converted = kwargs.get('size', False)

        fn_ext = os.path.splitext(track.path)[1]

        # As specified in Subsonic API: if maxBitRate is set to zero, no limit is imposed. We also
        # avoid any upsampling.
        if fn_ext[1:] == output_format and (not maxBitRate or maxBitRate >= track.bitrate):
            return http.send_file(track.path)

        Transcoder = request.env['oomusic.transcoder'].search(
            [('input_formats.name', '=', fn_ext[1:]), ('output_format.name', '=', output_format)],
            limit=1,
        )
        if Transcoder:
            generator = Transcoder.transcode(int(trackId), bitrate=maxBitRate).stdout
            mimetype = Transcoder.output_format.mimetype
        else:
            _logger.warning('Could not find converter from "%s" to "%s"', fn_ext[1:], output_format)
            return http.send_file(track.path)

        data = wrap_file(
            request.httprequest.environ, generator, buffer_size=Transcoder.buffer_size * 1024)
        return Response(data, mimetype=mimetype, direct_passthrough=True)

    @http.route(['/rest/download.view'], type='http', auth='public', csrf=False, methods=['GET', 'POST'])
    def download(self, **kwargs):
        rest = SubsonicREST(kwargs)
        success, response = rest.check_login()
        if not success:
            return response

        trackId = kwargs.get('id')
        if trackId:
            track = request.env['oomusic.track'].browse([int(trackId)])
            if not track.exists():
                return rest.make_error(code='70', message='Song not found')
        else:
            return rest.make_error(code='10', message='Required int parameter "id" is not present')

        return http.send_file(track.path, as_attachment=True)

    @http.route(['/rest/hls.view'], type='http', auth='public', csrf=False, methods=['GET', 'POST'])
    def hls(self, **kwargs):
        rest = SubsonicREST(kwargs)
        success, response = rest.check_login()
        if not success:
            return response

        return rest.make_error(code='30', message='Feature not supported by server.')

    @http.route(['/rest/getCaptions.view'], type='http', auth='public', csrf=False, methods=['GET', 'POST'])
    def getCaptions(self, **kwargs):
        rest = SubsonicREST(kwargs)
        success, response = rest.check_login()
        if not success:
            return response

        return rest.make_error(code='30', message='Feature not supported by server.')

    @http.route(['/rest/getCoverArt.view'], type='http', auth='public', csrf=False, methods=['GET', 'POST'])
    def getCoverArt(self, **kwargs):
        rest = SubsonicREST(kwargs)
        success, response = rest.check_login()
        if not success:
            return response

        folderId = kwargs.get('id')
        if folderId:
            try:
                if 'al-' in folderId:
                    folder = request.env['oomusic.album'].browse([int(folderId.split('-')[-1])])
                else:
                    folder = request.env['oomusic.folder'].browse([int(folderId.split('-')[-1])])
                if not folder.exists():
                    return rest.make_error(code='70', message='Folder not found')
            except:
                folder = request.env['oomusic.folder']
        else:
            return rest.make_error(code='10', message='Required int parameter "id" is not present')

        image = folder.image_medium or 'R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs='
        image_stream = StringIO.StringIO(image.decode('base64'))
        image_ext = '.' + (imghdr.what(image_stream) or 'png')
        return http.send_file(image_stream, filename=folderId + image_ext)

    @http.route(['/rest/getLyrics.view'], type='http', auth='public', csrf=False, methods=['GET', 'POST'])
    def getLyrics(self, **kwargs):
        rest = SubsonicREST(kwargs)
        success, response = rest.check_login()
        if not success:
            return response

        artist = kwargs.get('artist')
        title = kwargs.get('title')

        root = etree.Element('subsonic-response', status='ok', version=rest.version_server)
        xml_lyrics = rest.make_Lyrics(artist, title)
        root.append(xml_lyrics)

        return rest.make_response(root)

    @http.route(['/rest/getAvatar.view'], type='http', auth='public', csrf=False, methods=['GET', 'POST'])
    def getAvatar(self, **kwargs):
        rest = SubsonicREST(kwargs)
        success, response = rest.check_login()
        if not success:
            return response

        username = kwargs.get('username')
        if not username:
            return rest.make_error(
                code='10', message='Required str parameter "username" is not present')

        user = request.env['res.users'].search([('login', '=', username)])

        image = user.partner_id.image_medium or 'R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs='
        image_stream = StringIO.StringIO(image.decode('base64'))
        image_ext = '.' + (imghdr.what(image_stream) or 'png')
        return http.send_file(image_stream, filename=str(user.id) + image_ext)
