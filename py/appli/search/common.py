# -*- coding: utf-8 -*-
import os
import time
from pathlib import Path
from flask import render_template, json
from appli import app, gvg


@app.route('/common/ServerFolderSelect')
def ServerFolderSelect():
    res = []
    # the HTML id of the element which will be updated once selection is done
    target_id = gvg("target", "ServerPath")
    # noinspection PyUnresolvedReferences
    return render_template('common/fileserverpopup.html', root_elements=res,
                           targetid=target_id, ziponly=gvg('ZipOnly', 'N'))


@app.route('/common/ServerFolderSelectJSON')
def ServerFolderSelectJSON():
    server_root = Path(app.config['SERVERLOADAREA'])
    current_path = server_root
    parent = gvg("id")
    if parent != '#':
        current_path = server_root.joinpath(Path(parent))
    res = []
    for x in current_path.iterdir():
        rr = x.relative_to(server_root).as_posix()
        rc = x.relative_to(current_path).as_posix()
        try:
            if x.is_dir():
                if gvg('ZipOnly') == 'Y':
                    res.append(dict(id=rr, text="<span class=v>" + rc + "</span> ", parent=parent, children=True))
                else:
                    res.append(dict(id=rr,
                                    text="<span class=v>" + rc +
                                         "</span> <span class='TaxoSel label label-default'>Select</span>",
                                    parent=parent, children=True))
            if x.suffix.lower() == ".zip":
                fi = os.stat(x.as_posix())
                fmt = (rc, fi.st_size / 1048576, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(fi.st_mtime)))
                res.append(dict(id=rr,
                                text="<span class=v>" + "%s (%.1f Mb : %s)" % fmt +
                                     "</span> <span class='TaxoSel label label-default'>Select</span>",
                                parent=parent, children=False))
        except:
            pass  # le parcours des fichier peu planter sur system volume information par exemple.
    res.sort(key=lambda val: str.upper(val['id']), reverse=False)
    return json.dumps(res)
