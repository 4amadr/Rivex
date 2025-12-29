Esse diretório foi criado pois o callix tem uma coleta mais complexa.
O callix tem coleta de dados por requisição por API, mas para isso, precisamos coletar os tokens de cada ambiente 
há uma estimativa de aproximadamente 150 clientes, eu estou usando uma amóstra para testar sua funcionalidade e depois aplicar
em todos os clientes.


==== PASSOS ====
1 : Coleta de token(usando selenium):
A automação vai no ambiente, faz o login, vai até a área de API's e verifica se há tokens disponiveis
se houver tokens ele os coleta e envia para o banco de dados, se não houver nenhum token a automação vai criar um do zero
a instrução é para criar tokens com permições de administrador e após criar os tokens ele vai salvar no mesmo banco de dados

2 : Banco de dados(ainda em desenvolvimento):
Após a coleta dos toneks e enviar eles para o banco de dados, eu criei uma conexão com o banco para selecionar a tabela e o token por
cliente.
A ideia é ter os tokens de forma bem diferenciada para serem acessados posteriormente por API

3: API( aparentemente pronta, mas necessita da finalização das etapas anteriores):
a API vai usar cada token para coletar dados de seus respectivos ambientes
a lógica é buscar sempre nos dias de ontem(em dias de semana) e em caso de coletas em inicio de semana, a automação vai buscar
pela ultima sexta feira e sábado
futuramente a ideia é mudar a lógica para coletar dados apenas dos dias de ontem, mas a automação vai ser executada diariamente, independente do dia

4 banco de dados(ainda não criado):
enviar os dados de telefonia coletados por API para o banco de dados
