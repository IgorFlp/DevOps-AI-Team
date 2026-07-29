import os
import sys

# Ensure project root is in the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from crewai import Agent, Task, Crew
from core.llm_config import nexus_llm

# Agente SRE com foco em segurança
safety_sre = Agent(
    role='Safety_SRE',
    goal='Diagnosticar falhas e propor correções seguras no Kubernetes.',
    backstory='Você é um engenheiro sênior cauteloso. Você SEMPRE usa dry-run.',
    llm=nexus_llm,
    verbose=True
)

# Task que exige aprovação humana
task_remediation = Task(
    description="""
    Detectamos que o pod 'checkout-api' está com erro de imagem. 
    1. Gere o manifesto YAML de correção.
    2. Use a ferramenta 'executar_fix_k8s_com_segurança'
    3. SE O RETORNO DA FERRAMENTA FOR "CANCELADO", voce deve encerrar IMEDIATAMENTE e informar que a ação foi abortada pelo humano.
    PROIBIDO dizer que a aplicação foi concedida se o humano digitar 'não'
    4. SE O RETORNO DA FERRAMENTA FOR "SUCESSO", voce deve encerrar IMEDIATAMENTE e informar que a ação foi aplicada com sucesso
    PROIBIDO dizer que a aplicação foi abortada se o humano digitar 'sim'
    """,
    expected_output="O comando exato para correção e o resultado do dry-run.",
    agent=safety_sre
)

if __name__ == "__main__":
    # Simulando o Human-in-the-loop no terminal
    print("\n🚀 [NEXUS-BOT] Iniciando análise de remediação...")
    nexus_crew = Crew(agents=[safety_sre], tasks=[task_remediation], verbose=True)
    resultado = nexus_crew.kickoff()
    
    print(f"\n⚠️ PROPOSTA DA IA:\n{resultado}")
    aprovacao = input("\n✅ Você aprova a execução deste comando em PRODUÇÃO? (sim/não): ")
    
    if aprovacao.strip().lower() == 'sim':
        print("\n🔥 Executando comando... (Simulado)")
        print("Status: Pod 'checkout-api' atualizado com sucesso!")
    else:
        print("\n🛑 Operação ABORTADA pelo engenheiro. Registrando no log de auditoria.")