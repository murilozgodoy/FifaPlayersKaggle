% =============================================================================
% Knowledge Engine - FIFA Players
% Queries (Regras / Sentencas)
% =============================================================================
%
% Predicado base (gerado pelo ETL em base.pl):
%   jogador(Nome, Nacionalidade, Clube, Posicao, Idade, Overall, Potencial, Valor).
%
% Para usar: carregue base.pl E queries.pl no SWISH (cole tudo na area Program).
% =============================================================================


% =============================================================================
% PERGUNTA 1: Ranking de clubes por valor total de elenco
% -----------------------------------------------------------------------------
% "Quais os clubes mais valiosos, ordenados pelo valor total de seus jogadores?"
%
% Sofisticacao: agregacao (sum_list) + ordenacao (setof) + composicao de regras
%   - clube/1 lista todos os clubes unicos (predicado auxiliar)
%   - valor_clube/2 soma os valores dos jogadores de um clube
%   - ranking_clubes/1 ordena todos os clubes por valor total
% =============================================================================

% Predicado auxiliar: lista clubes (evita variavel livre no findall)
clube(Clube) :-
    jogador(_, _, Clube, _, _, _, _, _).

% Soma o valor de todos os jogadores de um clube
valor_clube(Clube, ValorTotal) :-
    clube(Clube),
    findall(V, jogador(_, _, Clube, _, _, _, _, V), Valores),
    sum_list(Valores, ValorTotal).

% Ranking dos clubes do mais valioso para o menos valioso
ranking_clubes(Ranking) :-
    setof(Valor-Clube, valor_clube(Clube, Valor), ListaCrescente),
    reverse(ListaCrescente, Ranking).

% Uso (na area Query do SWISH):
%   ?- ranking_clubes(R).
%   ?- valor_clube(real_madrid, V).


% =============================================================================
% PERGUNTA 2: Joias escondidas (jogadores jovens e promissores)
% -----------------------------------------------------------------------------
% "Quais jogadores sao 'joias': jovens (<=23 anos) com potencial maior que o
%  overall atual (diferenca >= 5)?"
%
% Sofisticacao: composicao de multiplas regras + comparacao aritmetica + filtros
%   - jovem/1, promissor/1 sao predicados auxiliares
%   - joia/3 combina os criterios e calcula a diferenca
%   - ranking_joias/1 ordena pelas maiores diferencas
% =============================================================================

% Auxiliar: jogador eh jovem se idade <= 23
jovem(Nome) :-
    jogador(Nome, _, _, _, Idade, _, _, _),
    Idade =< 23.

% Auxiliar: jogador eh promissor se potencial - overall >= 5
promissor(Nome, Diferenca) :-
    jogador(Nome, _, _, _, _, Overall, Potencial, _),
    Diferenca is Potencial - Overall,
    Diferenca >= 5.

% Joia = jovem E promissor (composicao das duas regras)
joia(Nome, Clube, Diferenca) :-
    jovem(Nome),
    promissor(Nome, Diferenca),
    jogador(Nome, _, Clube, _, _, _, _, _).

% Ranking das maiores joias (maior diferenca primeiro)
ranking_joias(Ranking) :-
    setof(Dif-(Nome, Clube), joia(Nome, Clube, Dif), ListaCrescente),
    reverse(ListaCrescente, Ranking).

% Uso (na area Query do SWISH):
%   ?- ranking_joias(R).
%   ?- joia(Nome, Clube, Dif).


% =============================================================================
% PERGUNTA 3: Top paises por overall medio (com minimo de jogadores)
% -----------------------------------------------------------------------------
% "Quais os paises com maior overall medio, considerando apenas paises com
%  pelo menos 5 jogadores no dataset?"
%
% Sofisticacao: agregacao dupla (count + media) + filtro condicional + ordenacao
%   - pais/1, conta_jogadores_pais/2, soma_overall_pais/2 sao auxiliares
%   - media_overall_pais/2 combina contagem e soma para calcular a media
%   - ranking_paises/1 aplica o filtro de minimo e ordena
% =============================================================================

% Auxiliar: lista paises unicos
pais(Pais) :-
    jogador(_, Pais, _, _, _, _, _, _).

% Conta quantos jogadores um pais tem no dataset
conta_jogadores_pais(Pais, Total) :-
    pais(Pais),
    findall(1, jogador(_, Pais, _, _, _, _, _, _), Lista),
    length(Lista, Total).

% Soma o overall de todos os jogadores de um pais
soma_overall_pais(Pais, Soma) :-
    pais(Pais),
    findall(O, jogador(_, Pais, _, _, _, O, _, _), Overalls),
    sum_list(Overalls, Soma).

% Calcula a media de overall de um pais (apenas se tiver >= 5 jogadores)
media_overall_pais(Pais, Media) :-
    conta_jogadores_pais(Pais, Total),
    Total >= 5,
    soma_overall_pais(Pais, Soma),
    Media is Soma / Total.

% Ranking dos paises por overall medio (do maior para o menor)
ranking_paises(Ranking) :-
    setof(Media-Pais, media_overall_pais(Pais, Media), ListaCrescente),
    reverse(ListaCrescente, Ranking).

% Uso (na area Query do SWISH):
%   ?- ranking_paises(R).
%   ?- media_overall_pais(brazil, M).
