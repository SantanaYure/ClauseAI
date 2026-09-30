"""Modelo neutro de documento: os renderizadores PDF e DOCX consomem os mesmos blocos."""

from dataclasses import dataclass, field
from typing import Literal

BlockKind = Literal[
    "title", "subtitle", "h1", "h2", "h3", "p", "item", "bullet", "table", "note", "pagebreak"
]
Status = Literal["C", "N", "E"]  # contratada, não contratada, excluída

STATUS_LABEL: dict[Status, str] = {"C": "Contratada", "N": "Não contratada", "E": "Excluída"}


@dataclass(frozen=True)
class Table:
    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    widths: tuple[float, ...] = ()
    caption: str = ""


@dataclass(frozen=True)
class Block:
    kind: BlockKind
    text: str = ""
    number: str = ""
    table: Table | None = None


@dataclass(frozen=True)
class Vocab:
    """Terminologia própria de cada seguradora (todas as formas em concordância masculina)."""

    T: str = "Tomador"
    S: str = "Segurado"
    S_pl: str = "Segurados"
    P: str = "Perdas"
    ato: str = "Ato Danoso"
    L: str = "Limite Máximo de Garantia"
    L_abbr: str = "LMG"
    a_name: str = "Cobertura A – Indenização ao Segurado"
    b_name: str = "Cobertura B – Reembolso ao Tomador"
    c_name: str = "Cobertura C – Reclamações de Mercado de Valores Mobiliários"


@dataclass(frozen=True)
class Cov:
    status: Status
    limit: str = "Até o LMG"
    deductible: str = "Conforme Cobertura B"
    note: str = ""


@dataclass(frozen=True)
class Endorsement:
    title: str
    paragraphs: tuple[str, ...]


@dataclass(frozen=True)
class Spec:
    stem: str
    variant: int
    # Seguradora e identificação
    insurer: str
    insurer_cnpj: str
    insurer_susep: str
    insurer_address: str
    ouvidoria: str
    apolice: str
    proposta: str
    processo: str
    emissao: str
    vig_ini: str
    vig_fim: str
    # Tomador e corretor
    tomador: str
    tomador_cnpj: str
    tomador_address: str
    tomador_profile: str
    corretor: str
    corretor_susep: str
    vocab: Vocab
    # Limites, franquias e prêmio
    lmg: int
    premio_liquido: int
    parcelas: int
    franquia_a: str
    franquia_b: str
    franquia_c: str
    participacao: str
    side_a_dic: int = 0
    # Prazos e território
    retro_style: Literal["ilimitada", "datada", "periodo"] = "ilimitada"
    retro_value: str = ""
    comp_months: int = 0
    comp_auto: bool = True
    comp_premium_pct: int = 0
    supl_months: int = 0
    supl_premium_pct: int = 0
    supl_deadline_days: int = 30
    runoff_months: int = 0
    runoff_text: str = ""
    notice_days: int = 30
    territory: str = "Mundial."
    jurisdiction: str = "Qualquer jurisdição, observada a Cláusula de Sanções."
    territory_style: Literal["mundial", "brasil", "mercosul", "mundial_eua"] = "mundial"
    # Foro e cláusulas de estilo
    arbitration: bool = False
    forum_city: str = "São Paulo/SP"
    pollution_style: Literal[
        "cleanup_only", "coverage", "absolute", "sidea_carveback", "standard"
    ] = "standard"
    cyber_exclusion: bool = False
    # Quadros
    coverages: dict[str, Cov] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    insureds: tuple[tuple[str, str], ...] = ()
    subsidiaries: tuple[tuple[str, str], ...] = ()
    endorsements: tuple[Endorsement, ...] = ()
    extra_exclusions: tuple[str, ...] = ()
