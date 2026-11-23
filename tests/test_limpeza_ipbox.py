from src.rivex.data_processing.IPBox.limpeza_ipbox import (
    gerar_html,
    gerar_lista_clientes,
    get_cliente,
    get_identificador,
)


def test_gerar_lista_clientes_inclui_linhas_linha1_e_linha2():
    html = """
    <table>
        <tr class="header"><th>Fila</th></tr>
        <tr class="linha1">
            <td nowrap=""><a href="editFila.php?act=alter&obj_fila_id=13">1133#01 - Hekos Consultoria</a></td>
        </tr>
        <tr class="linha2">
            <td nowrap=""><a href="editFila.php?act=alter&obj_fila_id=9">1314#01 - Luimar Consultoria</a></td>
        </tr>
        <tr class="linha1">
            <td nowrap=""><a href="editFila.php?act=alter&obj_fila_id=12">2101#01 - Samara Fernandes</a></td>
        </tr>
        <tr class="linha2">
            <td nowrap=""><a href="editFila.php?act=alter&obj_fila_id=52">2141#01 - Fs Consultoria</a></td>
        </tr>
        <tr class="linha2">
            <td nowrap=""><a href="editFila.php?act=alter&obj_fila_id=106">2470#01 - Paulinho Veiga</a></td>
        </tr>
        <tr class="rodape"><td>5 Registros - Página 1 de 1</td></tr>
    </table>
    """

    soup = gerar_html(html)
    linhas = gerar_lista_clientes(soup)

    nomes = [get_cliente(linha).strip() for linha in linhas]
    ids = [get_identificador(linha) for linha in linhas]

    assert nomes == [
        "1133#01 - Hekos Consultoria",
        "1314#01 - Luimar Consultoria",
        "2101#01 - Samara Fernandes",
        "2141#01 - Fs Consultoria",
        "2470#01 - Paulinho Veiga",
    ]
    assert ids == ["13", "9", "12", "52", "106"]
