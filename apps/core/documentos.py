"""
Versão dos documentos legais publicados em /termos/ e /privacidade/.

Ao mudar o texto de um documento (templates/core/termos.html ou
privacidade.html), atualize a versão e a data aqui. A entrega #11 (LGPD) pode
usar a versão para registrar qual texto cada usuário aceitou.

Origem do texto: os rascunhos em PDF da pasta Documents/, com as lacunas
preenchidas como projeto acadêmico e os trechos ajustados ao que o app faz.
"""

from datetime import date

# 1.1 (entrega #2): IA de verdade com o Groq e o aviso de não incluir dados de estudantes.
TERMOS_DE_USO = {"versao": "1.1", "atualizado_em": date(2026, 11, 27)}
# 1.1 (entregas #5 e #6): perfil de aprendizagem, sugestões de apoio da IA, quem e
# quando marcou a atenção, cadastro de estudantes também pelo núcleo e arquivamento.
# 1.2 (entrega #2): Groq como provedor de IA, retenção do provedor e transferência para os EUA.
POLITICA_DE_PRIVACIDADE = {"versao": "1.2", "atualizado_em": date(2026, 11, 27)}
