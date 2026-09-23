"""Catalog of ready-made script (roteiro) templates offered by the web UI (SPEC-003, RF-02)."""
from __future__ import annotations

TEMPLATES: list[dict[str, str]] = [
    {
        "id": "terror",
        "genre": "Terror",
        "title": "A Última Noite na Cabana",
        "synopsis": "Amigos isolados numa cabana percebem, tarde demais, que não estão sozinhos.",
        "promptText": (
            "Um grupo de amigos decide passar o fim de semana em uma cabana isolada no meio "
            "da floresta, longe de qualquer sinal de celular. Na primeira noite, ruídos "
            "estranhos começam a vir das árvores e uma sombra passa correndo pela janela. "
            "Aos poucos, cada um percebe que algo os observa há muito tempo, e a única saída "
            "é enfrentar o medo para sobreviver até o amanhecer."
        ),
    },
    {
        "id": "ficcao_cientifica",
        "genre": "Ficção Científica",
        "title": "Sinal de Kepler-9",
        "synopsis": "Uma tripulação espacial parte em missão após captar um sinal misterioso.",
        "promptText": (
            "Em um futuro próximo, uma pequena tripulação espacial capta um sinal de rádio "
            "vindo do sistema Kepler-9, a anos-luz da Terra. Decididos a investigar, eles "
            "embarcam em uma jornada arriscada através do espaço profundo, enfrentando falhas "
            "na nave, decisões difíceis e a descoberta de que o sinal esconde algo muito maior "
            "do que imaginavam sobre a origem da vida no universo."
        ),
    },
    {
        "id": "drama",
        "genre": "Drama",
        "title": "O Último Verão com Meu Pai",
        "synopsis": "Um reencontro entre pai e filho depois de anos de distância.",
        "promptText": (
            "Depois de anos sem se falar, um filho decide visitar o pai, que mora sozinho numa "
            "casa simples no interior. O verão que deveria ser breve se transforma em uma "
            "jornada de reconciliação, onde memórias antigas, mágoas guardadas e pequenos "
            "gestos de carinho os ajudam a reconstruir, aos poucos, o vínculo que o tempo "
            "havia desgastado."
        ),
    },
    {
        "id": "romance",
        "genre": "Romance",
        "title": "Cartas Que Nunca Enviei",
        "synopsis": "Dois amigos de infância se reencontram anos depois por acaso.",
        "promptText": (
            "Anos atrás, dois amigos de infância prometeram se reencontrar, mas a vida os "
            "levou para caminhos diferentes. Quando o destino os coloca frente a frente "
            "novamente em uma pequena cidade litorânea, sentimentos que pareciam esquecidos "
            "voltam à tona, e os dois precisam decidir se estão dispostos a arriscar tudo por "
            "uma segunda chance no amor."
        ),
    },
    {
        "id": "comedia",
        "genre": "Comédia",
        "title": "Confusão no Casamento",
        "synopsis": "Uma série de mal-entendidos hilários ameaça o casamento dos sonhos.",
        "promptText": (
            "No dia do casamento dos sonhos, tudo que pode dar errado, dá errado: o bolo "
            "derrete no calor, o padrinho perde as alianças e um convidado errado aparece "
            "vestido igual ao noivo. Em meio à confusão total, os noivos e a família precisam "
            "improvisar soluções cada vez mais absurdas para salvar a festa antes que os "
            "convidados percebam o caos nos bastidores."
        ),
    },
]


def get_templates() -> list[dict[str, str]]:
    """Returns the 5 ready-made script templates (GET /api/templates)."""
    return TEMPLATES


def get_template_by_id(template_id: str) -> dict[str, str] | None:
    return next((t for t in TEMPLATES if t["id"] == template_id), None)
