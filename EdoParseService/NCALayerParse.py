from pywinauto.application import Application
from pywinauto.mouse import click
from pywinauto.keyboard import send_keys

import EdoParseService.ecp_info as ecp


def get_coords(element):
    rect = element.rectangle()

    center_x = (rect.left + rect.right) // 2
    center_y = (rect.top + rect.bottom) // 2

    return (center_x, center_y)


def choose_ECP(element):
    click(coords=get_coords(element))
    send_keys(ecp.path)
    send_keys('{ENTER}')


def enter_password(element):
    element.click_input()
    element.type_keys(ecp.password)


def Start():
    app = Application(backend="uia").connect(title='NCALayer')

    choose_ECP(app.NCALayer.Button5)
    enter_password(app.NCALayer.Edit2)
    app.NCALayer.Button7.click()

    click(coords=get_coords(app.NCALayer.ListBox.ListItem))
    app.NCALayer.Button4.click()

