from datetime import datetime

def payload_login(usuario, senha, viewstate):
    return {
        "j_id27": "j_id27",
        "j_id27:login": usuario,
        "j_id27:password": senha,
        "j_id27:j_id42": "Acessar Portal",
        "javax.faces.ViewState": viewstate
    }

def header_sippulse():
    return {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0"
    }
def payload_chamadas_tarifadas(data, viewstate):

    data_obj = datetime.strptime(data, "%d/%m/%Y")
    mes_ano = data_obj.strftime("%m/%Y")

    return {
        "AJAXREQUEST": "_viewRoot",

        "frmAsrSub:datefromInputDate": f"{data} 00:00",
        "frmAsrSub:datefromInputCurrentDate": mes_ano,

        "frmAsrSub:datetoInputDate": f"{data} 23:59",
        "frmAsrSub:datetoInputCurrentDate": mes_ano,

        "frmAsrSub:datetoTimeHours": "23",
        "frmAsrSub:datetoTimeMinutes": "59",

        "frmAsrSub:pagination": "50",
        "frmAsrSub:filterData": "",
        "frmAsrSub:callerId": "",
        "frmAsrSub:callId": "",

        "frmAsrSub": "frmAsrSub",
        "autoScroll": "",

        "javax.faces.ViewState": viewstate,

        "frmAsrSub:j_id117": "frmAsrSub:j_id117"
    }

def payload_dados_monetarios(data, viewstate):

    mes_ano = datetime.strptime(data, "%d/%m/%Y").strftime("%m/%Y")

    return {
        "frmCdr": "frmCdr",
        "frmCdr:panelDados": "tabFilter",
        "frmCdr:datefromInputDate": data,
        "frmCdr:datefromInputCurrentDate": mes_ano,
        "frmCdr:datetoInputDate": data,
        "frmCdr:datetoInputCurrentDate": mes_ano,
        "frmCdr:pagination": "50",
        "frmCdr:filterData": "",
        "frmCdr:j_id100": "Gerar Relatório",
        "javax.faces.ViewState": viewstate,
    }
    
    
def payload_pagina_inicial(viewstate):
    return {
        "frmMenu": "frmMenu",
        "panelMenuStatefrmMenu:j_id37": "opened",
        "panelMenuActionfrmMenu:j_id37": "",
        "panelMenuActionfrmMenu:j_id38": "",
        "panelMenuActionfrmMenu:j_id39": "",
        "frmMenu:j_id39": "",
        "panelMenuStatefrmMenu:j_id40": "opened",
        "panelMenuActionfrmMenu:j_id40": "",
        "panelMenuActionfrmMenu:j_id43": "",
        "panelMenuActionfrmMenu:j_id46": "",
        "panelMenuStatefrmMenu:j_id47": "opened",
        "panelMenuActionfrmMenu:j_id47": "",
        "panelMenuActionfrmMenu:j_id48": "",
        "panelMenuActionfrmMenu:j_id49": "",
        "panelMenuActionfrmMenu:j_id50": "",
        "panelMenuActionfrmMenu:j_id51": "",
        "panelMenuStatefrmMenu:j_id53": "opened",
        "panelMenuActionfrmMenu:j_id53": "",
        "panelMenuActionfrmMenu:j_id54": "",
        "frmMenu:j_id36selectedItemName": "j_id39",
        "javax.faces.ViewState": viewstate,
    }
    
    
def payload_navegacao_chamadas_tarifadas(viewstate):
    return {
        "frmMenu": "frmMenu",

        "panelMenuStatefrmMenu:j_id37": "opened",
        "panelMenuActionfrmMenu:j_id37": "",

        "panelMenuActionfrmMenu:j_id38": "",
        "panelMenuActionfrmMenu:j_id39": "",

        "panelMenuStatefrmMenu:j_id40": "opened",
        "panelMenuActionfrmMenu:j_id40": "",

        "panelMenuActionfrmMenu:j_id43": "",
        "panelMenuActionfrmMenu:j_id46": "",

        "panelMenuStatefrmMenu:j_id47": "opened",
        "panelMenuActionfrmMenu:j_id47": "",

        "panelMenuActionfrmMenu:j_id48": "",
        "panelMenuActionfrmMenu:j_id49": "",
        "panelMenuActionfrmMenu:j_id50": "",
        "panelMenuActionfrmMenu:j_id51": "",

        "panelMenuStatefrmMenu:j_id53": "opened",
        "panelMenuActionfrmMenu:j_id53": "",
        "panelMenuActionfrmMenu:j_id54": "",

        "frmMenu:j_id36selectedItemName": "j_id48",

        "javax.faces.ViewState": viewstate
    }