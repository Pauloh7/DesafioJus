import re


def remove_blank_space(txt):
    """"""
    array = txt.split()
    return " ".join(array).strip()


def remove_special_characters(texto):
    """"""
    texto_corrigido = texto
    texto_corrigido = re.sub(
        r"[\\\/,;<>\.\?\/\!\*\-\+\_\=\@\#%:\(\)" "]+", "", texto_corrigido
    )
    texto_corrigido = re.sub(r"\(\)", "", texto_corrigido)
    texto_corrigido = re.sub(r"\s{2,}", " ", texto_corrigido)
    texto_corrigido = re.sub(r"^\s+", "", texto_corrigido)
    texto_corrigido = re.sub(r"\s+$", "", texto_corrigido)
    return texto_corrigido
