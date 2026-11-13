# review

Ferramenta de aprovação dos cronogramas de social media da Everest. Substitui o Google Slides: o cliente comenta direto na peça e a agência controla status e o que vai ser animado.

## Como o app roda

O app é o `index.html`, publicado como Artifact do claude.ai:
https://claude.ai/artifact/Exmy9mGbdcAUQcoWwid7cS

Ele usa três recursos da plataforma, acessados por `window.claude.use(...)`:

| Recurso  | Para quê                                                        |
|----------|-----------------------------------------------------------------|
| `db`     | status, marcação de animação, comentários, notificações, perfis |
| `user`   | identifica quem está vendo (nome e foto) e busca pessoas no `@` |
| `assets` | vídeos e imagens enviados pelo admin dentro de um post          |

Aberto fora do claude.ai, o app entra em modo demonstração e não salva nada.

## Estrutura

```
index.html                o app inteiro (HTML, CSS e JS num arquivo só)
img/                      artes de novembro, exportadas da página NOVEMBRO do Figma
vid/                      capas dos vídeos de novembro, recortadas do Google Slides (nome = id do arquivo no Drive)
sp/                       imagens dos outros meses, tiradas dos slides, em folhas de 16 peças (<mês>-N.jpg)
data/posts-<mês>.json     cópia legível dos posts de cada mês, que estão embutidos no index.html
tools/import_month.py     importa um deck do Google Slides para data/ e sp/
```

## Telas

- **Cronogramas**: canvas navegável com um aglomerado por mês.
- **Mês**: três visualizações do mesmo conteúdo: Slides (um slide por post), Calendário e Lista.
- **Post**: gaveta lateral com criativo, arquivos finais do Drive, legenda, insight e comentários. Clicar numa peça fixa o comentário naquele ponto.
- **Notificações** e **Pessoas**: avisos de `@` e perfis (Admin, Usuário, Cliente).

## Modelo de dados

Os posts (data, formato, legenda, insight, artes, vídeos, arquivos finais) ficam na constante `POSTS` do `index.html`. O que muda com o uso fica no banco:

- **state/{postId}**: `status`, `animar`, `media[]` (arquivos enviados: `id`, `kind`, `name`), `by`, `ts`
- **comments/{id}**: `postId`, `by`, `text`, `ts`, `pin` (`k` = peça, `x`, `y` em %), `done`, `mentions[]`
- **notifs/{id}**: `to`, `by`, `postId`, `commentId`, `text`, `ts`, `read`, `emailed`
- **members/{userId}**: `firstSeen`, `role` (`admin` | `equipe` | `cliente`)

Regras de acesso: `state` e `members` só são alterados por quem pode editar o artifact; `comments` e `notifs` por qualquer pessoa com acesso de interação; cada pessoa registra o próprio `members/{id}`. O perfil em `members` é um rótulo: a permissão real vem do nível de compartilhamento do artifact.

## De onde vem o conteúdo

- Textos e status: decks "CRONOGRAMA EVEREST | <MÊS> 2026" do Google Slides, de maio a dezembro.
- Novembro: artes do Figma "Everest - Social Ciclos" (página NOVEMBRO) e arquivos finais da pasta `11_NOVEMBRO` do Drive.
- Outros meses: imagens que estão nos próprios slides. Vídeos aparecem sem capa, com link para o Drive.

## Pendências

- Capas de vídeo e arquivos finais do Drive para os meses fora de novembro.
- Janeiro a abril de 2026 (os decks existem no Drive, ainda não importados).
- Criar e editar posts pelo app.
- Notificação por e-mail (a plataforma não envia; precisa de servidor próprio).
