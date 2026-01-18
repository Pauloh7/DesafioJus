class Processo:
    def __init__(self, npu,grau, juiz, assunto, classe, area, data_distribuicao, valor_da_acao, partes, movimentos ):
        self.npu = npu
        self.grau = grau
        self.juiz = juiz
        self.assunto = assunto
        self.classe = classe
        self.area = area
        self.data_distribuicao = data_distribuicao
        self.valor_da_acao = valor_da_acao
        self.partes = partes
        self.movimentacoes = movimentos