from __future__ import annotations

from .identity import IdentityPlugin
from .chain_continuity import ChainContinuityPlugin
from .paragraph_paratope import ParagraphParatopePlugin
from .interface_contacts import InterfaceContactsPlugin

BUILTIN_PLUGINS = {
    "identity": IdentityPlugin(),
    "chain_continuity": ChainContinuityPlugin(),
    "paragraph_paratope": ParagraphParatopePlugin(),
    "interface_contacts": InterfaceContactsPlugin(),
}

__all__ = ["BUILTIN_PLUGINS"]
