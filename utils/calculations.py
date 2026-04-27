def calcul_cnas(salaire_brut):
    cnas_employe = salaire_brut * 0.09
    cnas_employeur = salaire_brut * 0.26
    return cnas_employe, cnas_employeur


def calcul_cacobatph(salaire_brut):
    return salaire_brut * 0.01


def calcul_g50(salaire_brut):
    if salaire_brut <= 30000:
        return salaire_brut * 0.10
    elif salaire_brut <= 120000:
        return salaire_brut * 0.20
    else:
        return salaire_brut * 0.35


def salaire_net(salaire_brut):
    cnas_emp, _ = calcul_cnas(salaire_brut)
    g50 = calcul_g50(salaire_brut)
    return salaire_brut - cnas_emp - g50
