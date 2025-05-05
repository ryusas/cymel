# -*- coding: utf-8 -*-
u"""
UI以外の全機能。

以下が全て並列に展開され簡単にアクセスできる（ cymel.ui 以外の全て）。

- 現在のセレクションを表す `~.ModuleForSel.sel` や `~.ModuleForSel.selection` 。
- cymel.core 以下の全て（主要なノードクラスや、データタイプなど）。
- 全てのノードクラスにアクセス可能な ``nt`` （ `.NodeTypes` のインスタンスの別名）。
- Maya新旧バージョン互換のためのノードタイプ名マップ ``cntm`` ( `.CompatNodeTypeMap` のインスタンスの別名）。
- cymel.constants の全て。
- cymel.pyutils 以下の全て。
- cymel.utils 以下の全て。
- cymel.initmaya の全て。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .core import *
from .compat_nodetype import *
from .constants import *
from .pyutils import *
from .utils import *
from .initmaya import *
nt = nodetypes
cntm = compat_nodetype_map
ModuleForSel(__name__)
