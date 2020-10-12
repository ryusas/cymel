# -*- coding: utf-8 -*-
u"""
UI以外の全機能。

以下が全て並列に展開され簡単にアクセスできる（ cymel.ui 以外の全て）。

- 現在のセレクションを表す `~.ModuleForSel.sel` や `~.ModuleForSel.selection` 。
- cymel.core 以下の全て（主要なノードクラスや、データタイプなど）。
- 全てのノードクラスにアクセス可能な ``nt`` （ `.NodeTypes` のインスタンスの別名）。
- cymel.constants の全て。
- cymel.pyutils 以下の全て。
- cymel.utils 以下の全て。
- cymel.initmaya の全て。
"""
from .core import *
from .constants import *
from .pyutils import *
from .utils import *
from .initmaya import *
nt = nodetypes
ModuleForSel(__name__)
