# MBA de Arquitetura de Sistemas Digitais - Faculdade Impacta
### Disciplina de Data Engineering & Architecture

- Aluno: Renan Baisso
- Professor: Lorran Santos Rodrigues
- Data: 14/11/2026

---

### Atividade Final da Disciplina
#### Enunciado:
📌 Objetivo

Evoluir ou modificar a plataforma usada em aula (https://github.com/lorransr/toy-data-platform), aplicando na prática o que vimos na disciplina: ingestão, orquestração, transformação, modelagem, camada semântica e consumo de dados.

A dica é partir de uma pergunta sobre os dados e mudar a plataforma para conseguir respondê-la. Exemplo: "Quais gêneros cresceram na Netflix depois de 2015, e a nota média acompanhou?" Ter uma pergunta deixa o trabalho mais concreto e mais fácil de explicar.


🤖 Sobre agentes de IA

Pode usar à vontade. Saber trabalhar com agentes faz parte da profissão hoje. O que eu quero ver no relatório é que você entendeu o que foi feito: por que escolheu um caminho, o que deu errado e como resolveu.


💡 Ideias (pode propor outra coisa)

- Ingestão: nova fonte com dlt; carga incremental (merge) no lugar de replace.
- Orquestração: DAG no Airflow encadeando dlt → dbt; integração com Cosmos.
- Transformação/modelagem: modelo incremental no dbt; snapshot; nova dimensão ou fato.
- Qualidade: novos testes no dbt (grão, frescor, contratos).
- Camada semântica: nova medida ou dimensão no Cube, usada no Superset e no agente via MCP.
- Consumo: novo dashboard no Superset; nova ferramenta no servidor MCP.
- Arquitetura: qualquer melhoria que resolva um problema que você notou.


📄 Entrega

Até 18/11, no Classroom: um relatório técnico em PDF ou DOCX.

Se o seu código estiver no GitHub, coloque o link no relatório. Não é obrigatório.


📝 O que o relatório deve ter

1. O que foi feito e por quê: o objetivo e, se tiver, a pergunta que você respondeu.
2. Como foi feito: o que mudou na plataforma e as principais decisões. Vale contar quais alternativas você considerou. Inclua os trechos de código mais importantes (o modelo dbt, a DAG, a medida no Cube etc.) e explique o que eles fazem.
3. Evidências: prints, logs, DAGs, modelos, dashboards. Se fez testes, mostre um deles pegando um erro de verdade.
4. Dificuldades: algum problema que apareceu no caminho e como você resolveu.
5. Uso de IA: como você usou os agentes, onde ajudaram e onde atrapalharam.
6. Aprendizados.

Seja direto. Um relatório curto e específico vale mais que um longo e genérico.


🎯 Critérios de avaliação

- Correção técnica: a implementação funciona e faz sentido.
- Qualidade da implementação: o código mostrado é claro e segue o padrão da plataforma.
- Clareza da explicação: dá para entender o que você fez e por quê.
- Evidências: os prints e os logs mostram a coisa funcionando de verdade.
- Organização do relatório.