from datetime import date, timedelta

from briefing import config
from briefing.models import Confidence, DCMSignalDraft, OpportunityType, SourceType
from briefing.summarize.dcm_score import band_of, day_temperature, dedup_and_score, score_signal

TAX = config.load_yaml("dcm_signals.yaml")
TODAY = date(2026, 11, 4)


def _draft(**kw):
    base = {"company": "Cia Exemplo Saneamento S.A.", "sector": "saneamento", "opportunity": OpportunityType.CONSENT_WAIVER,
                "subtype": "agd_convocada", "source_type": SourceType.DOCUMENTO_OFICIAL, "confidence": Confidence.ALTA,
                "evidence": "convoca AGD para deliberar sobre waiver", "reading": "waiver em curso", "next_step": "ler edital",
                "source_name": "CVM IPE", "url": "https://rad.cvm.gov.br/x"}
    base.update(kw)
    return DCMSignalDraft(**base)


def test_agd_proxima_fica_quente():
    s = score_signal(_draft(event_date=TODAY + timedelta(days=5), amount_brl=5e8), TAX, TODAY)
    # base 35 + urgência 20 + tamanho 10 + fonte 15 + setor 5 = 85
    assert s.score == 85 and s.band == "fervendo" and s.heat == 5


def test_rumor_macro_fica_frio():
    s = score_signal(_draft(opportunity=OpportunityType.MACRO_REGULATORIO, subtype="juros", sector="macro",
                            source_type=SourceType.RUMOR, confidence=Confidence.BAIXA), TAX, TODAY)
    assert s.band == "frio"


def test_dedup_conta_corroboracao():
    a = _draft(url="https://a")
    b = _draft(url="https://b", source_type=SourceType.IMPRENSA_PRINCIPAL)
    out = dedup_and_score([a, b], TAX, TODAY)
    assert len(out) == 1 and out[0].corroborations == 1 and out[0].source_type == SourceType.DOCUMENTO_OFICIAL


def test_taxonomia_consistente():
    for fam in TAX["signals"].values():
        for st in fam["subtypes"].values():
            assert 0 <= st["base"] <= 40 and st["keywords"]
    assert band_of(0) == "frio" and band_of(80) == "fervendo"
    assert day_temperature([]) == (0, "frio")
