# SomaAreaPoligonais.py
# Plugin TQS EAG V25 - Somatório de áreas de poligonais fechadas selecionadas
#
# Instalação: copiar este arquivo para TQSW\EXEC\Python\
# Menu:       incluir SomaAreaPoligonais.PYMEN no EAG.PYMEN via diretiva INCLUIR

from TQS import TQSDwg, TQSEag, TQSGeo


def soma_area_poligonais(eag, tqsjan):
    """
    Lista o somatório de áreas de todos os objetos selecionados que sejam
    poligonais fechadas. Elementos que não sejam poligonais fechadas recebem
    aviso e são ignorados.

    Assinatura padrão de rotina chamada pelo editor EAG:
        eag     - objeto TQSEag.Eag (acesso ao editor gráfico)
        tqsjan  - objeto TQSJan.Window (janela/desenho ativo)
    """
    eag.msg.ClearMessageWindow()
    eag.msg.Print("=== Somatório de Áreas de Poligonais Fechadas ===")

    dwg = tqsjan.dwg

    # Solicita seleção múltipla ao usuário
    addr, x, y, np_val, istat = eag.locate.Select(
        tqsjan,
        "Selecione os objetos (ponto ou janela), <Enter> para encerrar:",
        TQSEag.EAG_IMULTP,
    )

    if istat != 0:
        eag.msg.Print("Nenhum objeto selecionado.")
        eag.msg.PrintStatus("Nenhum objeto selecionado.")
        return

    # Prepara iteração sobre a lista de elementos selecionados
    eag.locate.BeginSelection(tqsjan)

    total_area = 0.0
    count_valid = 0
    count_invalid = 0

    while True:
        handle = eag.locate.NextSelection(tqsjan)
        if handle is None:
            break

        # Posiciona o iterator no elemento selecionado e lê seu tipo
        dwg.iterator.SetPosition(handle)
        itype = dwg.iterator.Next()

        # --- Verificação 1: deve ser uma poligonal ---
        if itype != TQSDwg.DWGTYPE_POLYLINE:
            count_invalid += 1
            eag.msg.Print(
                f"  AVISO: Elemento ignorado - não é poligonal "
                f"(tipo: {dwg.iterator.elementName})."
            )
            continue

        n_pts = dwg.iterator.xySize

        # --- Verificação 2: deve ser fechada ---
        # Uma poligonal é fechada se:
        #   a) isFilled == 1  (PolylineFilled - fechada implicitamente), OU
        #   b) o primeiro ponto é igual ao último ponto
        is_filled = bool(dwg.iterator.isFilled)
        is_closed = is_filled

        if not is_closed and n_pts >= 2:
            x0, y0 = dwg.iterator.GetPolylinePt(0)
            xn, yn = dwg.iterator.GetPolylinePt(n_pts - 1)
            if TQSGeo.Equals(x0, y0, xn, yn):
                is_closed = True

        if not is_closed:
            count_invalid += 1
            eag.msg.Print("  AVISO: Poligonal aberta ignorada.")
            continue

        # --- Verificação 3: pontos suficientes para delimitar área ---
        # isFilled: 3 pontos únicos = triângulo (mínimo 3 pts)
        # first==last: 3 pontos únicos = triângulo (mínimo 4 pts, sendo 1=último)
        min_pts = 3 if is_filled else 4
        if n_pts < min_pts:
            count_invalid += 1
            eag.msg.Print(
                f"  AVISO: Poligonal com pontos insuficientes ignorada "
                f"({n_pts} ponto(s))."
            )
            continue

        # --- Cálculo da área ---
        # iterator.xy retorna a lista completa no formato [[x0,y0], [x1,y1], ...]
        pts = dwg.iterator.xy
        vecx = [pt[0] for pt in pts]
        vecy = [pt[1] for pt in pts]

        # TQSGeo.Area retorna área com sinal (positivo = sentido horário)
        area = abs(TQSGeo.Area(vecx, vecy))
        total_area += area
        count_valid += 1
        eag.msg.Print(f"  Polígono {count_valid}: área = {area:.4f} cm²")

    # --- Resultado final ---
    eag.msg.Print("")
    eag.msg.Print(f"Polígonos válidos processados : {count_valid}")
    if count_invalid > 0:
        eag.msg.Print(f"Elementos ignorados (avisos)  : {count_invalid}")
    eag.msg.Print(f"SOMATÓRIO TOTAL DE ÁREAS     : {total_area:.4f} cm²")
    eag.msg.PrintStatus(f"Área total = {total_area:.4f} cm²")
