# review

O app é o `index.html`, publicado como o artifact https://claude.ai/artifact/Exmy9mGbdcAUQcoWwid7cS. O `README.md` descreve as telas e o modelo de dados.

Ao mudar o app:

1. Edite o `index.html` direto (não há etapa de build).
2. Publique nesse mesmo URL (Artifact, com `url`), com `root` na raiz do repositório. Envie em `files` apenas as imagens novas de `img/`, `vid/` e `sp/`; as já publicadas são mantidas.
3. Não passe `capabilities` no publish, para manter as declaradas (`db` com 5 regras, `user` com scope `profile`, `assets`). Se precisar mudar regras, redeclare o conjunto inteiro, como está no README.
4. Faça o commit aqui.

Se mudar a constante `POSTS`, atualize também o `data/posts-<mês>.json` correspondente.

Para importar ou reimportar um mês: leia o deck com a API do Google Slides (campos de texto, `size`, `transform`, `image.contentUrl` e `video`), rode `tools/import_month.py <json> <mês>` em seguida (os links das imagens expiram em cerca de 30 minutos) e recoloque os posts do mês na constante `POSTS`.
