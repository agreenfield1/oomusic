# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class MusicAlbum(models.Model):
    _name = 'oomusic.album'
    _description = 'Music Album'
    _order = 'year desc, name'

    create_date = fields.Datetime(index=True)

    name = fields.Char('Album', index=True)
    track_ids = fields.One2many('oomusic.track', 'album_id', 'Tracks')
    artist_id = fields.Many2one('oomusic.artist', 'Artist')
    genre_id = fields.Many2one('oomusic.genre', 'Genre')
    year = fields.Char('Year', index=True)
    folder_id = fields.Many2one('oomusic.folder', 'Folder', required=True, ondelete='cascade')
    user_id = fields.Many2one(
        'res.users', string='User', index=True, required=True, ondelete='cascade',
        default=lambda self: self.env.user
    )
    in_playlist = fields.Boolean('In Current Playlist')

    star = fields.Selection(
        [('0', 'Normal'), ('1', 'I Like It!')], 'Favorite', default='0')
    rating = fields.Selection(
        [('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')],
        'Rating', default='0',
    )

    image_folder = fields.Binary('Folder Image', related='folder_id.image_folder')
    image_big = fields.Binary("Big-sized image", related='folder_id.image_big')
    image_medium = fields.Binary("Medium-sized image", related='folder_id.image_medium')
    image_small = fields.Binary("Small-sized image", related='folder_id.image_small')
    image_small_cache = fields.Binary("Small-sized image", related='folder_id.image_small_cache')

    def _compute_in_playlist(self):
        for album in self:
            in_playlist = all(t.in_playlist for t in album.track_ids)
            if album.in_playlist != in_playlist:
                album.in_playlist = in_playlist

    @api.multi
    def action_add_to_playlist(self):
        playlist = self.env['oomusic.playlist'].search([('current', '=', True)], limit=1)
        if not playlist:
            raise UserError(_('No current playlist found!'))
        if self.env.context.get('purge'):
            playlist.action_purge()
        for album in self:
            playlist._add_tracks(album.track_ids)
