
.. _gettingstarted:

=======================================================
  cymel入門
=======================================================

.. _gettingstarted-import:

インポート
====================================
cymel の機能は以下の3つを選択してインポートできます。

- UI以外の全機能 `cymel.main`
- UIに関する機能 `cymel.ui`
- 任意でグローバルに展開すると便利なごく僅かな定数 `cymel.constants`

以下のようにインポートするのがおすすめです。

.. code-block:: python

    import cymel.main as cm
    import cymel.ui as cmu
    from cymel.constants import *

`cymel.constants` は `cymel.main` 内にも展開されているため、グローバルスコープを汚すことを嫌う場合はインポートしなくても構いません。

また、以下のように `cymel.all` をインポートするだけで、すべてのインポートを一度に行うこともできます。
上記といくつかの推奨モジュールがインポートされます。

.. code-block:: python

    from cymel.all import *

スタンドアロン Python (mayapy) で cymel をインポートすると、
`cymel.initmaya` モジュールの働きによって Maya が初期化されます。

.. note::
    本来の maya.standalone モジュールの initialize では userSetup.py は呼ばれますが userSetup.mel は呼ばれません。
    cymel による初期化ではそれを補い、 userSetup.mel も呼ばれるようにしています。

    ちなみに、pymel.core をインポートすると Maya UI を起動したのに近い、さらに多くのことがされます（たとえば、プラグインの自動ロードなど）。
    cymel では、あえてそこまではやらず、ごく最低限のことに留めています。



.. _gettingstarted-nodes:

ノードのラッパークラス
====================================
ノードオブジェクトの取得
-------------------------------------------
cymel は、プラグインも含まれる全てのノードタイプのラッパークラスを提供します。

全てのノードクラスは `.CyObject` を基底クラスとし、ノードタイプのツリーに沿って継承されています。
ノードをラップしたオブジェクトを得るには `.CyObject` コンストラクタを利用するのが簡単です。

たとえば、以下のようにノード名を指定します。

>>> cm.CyObject('persp')
Transform('persp')

pymel をご存知なら PyNode に相当するのが `.CyObject` です。

`.CyObject` には、別名 `.O` でもアクセスできます。

>>> cm.O('persp')
Transform('persp')

選択されているノードの場合はもっと簡単です。

選択ノードを1つ得るには `~.ModuleForSel.sel` を使います（複数選択されていても最初の1つとなります）。

>>> cmds.select(['persp', 'side'])
>>> cm.sel
Transform('persp')

または `~.ModuleForSel.selobj` 関数ではインデックスを指定できます。

>>> cm.selobj(1)
Transform('side')

選択されているものをすべて得るには `~.ModuleForSel.selection` か、または pymel 風に `~.ModuleForSel.selected` 関数を使います。

>>> cm.selection
[Transform('persp'), Transform('side')]
>>> cm.selected()
[Transform('persp'), Transform('side')]


.. _gettingstarted-nodes-command:

ノードクラスによる操作
-------------------------------------------
全てのノードクラスは `.NodeTypes` のインスタンスである `cm.nt <.NodeTypes>` からアクセスできます
（ごく一部の代表的なノードクラスは `cm <cymel.main>` からでもアクセスできます）。
クラス名は、ノードタイプ名の先頭を大文字にした名前となります。

>>> cm.nt.Joint
<class 'cymel.core.typeregistry.Joint'>

ノードクラスに既存ノードの名前を指定しないと、新規にノードが生成されます。

>>> cm.nt.Joint()
Joint('joint1')

これには :mayacmd:`createNode` コマンドのオプション引数を指定できます。

>>> cm.nt.Joint(n='foo#')
Joint('foo1')

また、ノードクラスは :mayacmd:`ls` コマンドのラッパーとしても機能します。

>>> cm.nt.Joint.ls()
[Joint('foo1'), Joint('joint1')]

:mayacmd:`ls` コマンドに -type オプションが自動的に指定された結果を得られますが、その他のオプション引数は自由に指定できます。

>>> cm.nt.Joint.ls('foo*')
[Joint('foo1')]


.. _gettingstarted-nodes-class:

ノードクラスを明示したオブジェクト取得
-------------------------------------------
既存のノード名を指定してラッパーオブジェクトを得るとき `.CyObject` ではないノードクラスを直接指定することもできます。

>>> cm.nt.Joint('foo1')
Joint('foo1')

このとき、互換性のある（継承している）クラスなら全て指定できます（上位になるほど抽象的になり、サポートされる機能が少なくなります）。

>>> cm.nt.Transform('foo1')
Transform('foo1')

ただし、互換性のないクラスを指定するとエラーになります。
たとえば、 :mayanode:`joint` は :mayanode:`transform` でもありますが :mayanode:`shape` ではないので、 `.Shape` クラスを指定するとエラーになります。

やはり、通常は、クラスを明示するよりも `.CyObject` を指定するのが簡単で確実です。
クラスの明示は、 :ref:`gettingstarted-customclasses-nodes` を作り未登録のまま使う場合や、あえて抽象的な振る舞いをさせたいような場合に使用します。
たとえば、 `.DagNode` 派生クラスは DAGパスを含んでいるため、同一ノードのインスタンスでもパスが異なれば違うものとして扱われます。
しかし、より抽象的な `.Node` インスタンスとして扱えば、DAGパスは含まれないため、同じものになります。

>>> cmds.file(f=True, new=True)
u'untitled'
>>> cmds.polyCube()
[u'pCube1', u'polyCube1']
>>> cmds.instance()
[u'pCube2']
>>> cm.O('pCube1|pCubeShape1') == cm.O('pCube2|pCubeShape1')
False
>>> cm.Node('pCube1|pCubeShape1') == cm.Node('pCube2|pCubeShape1')
True

あるノードがあるノードタイプの派生タイプかどうかを調べたい場合、以下のように Python の insinstance が利用できると思われるかもしれません。

>>> isinstance(cm.O('initialShadingGroup'), cm.nt.ObjectSet)
True

しかし、先に説明したように、抽象的なノードクラスを明示してそのインスタンスを取得できるということは、
以下のように isinstance ではノードタイプを厳密に判別できないことにもなります。

>>> isinstance(cm.nt.Node('initialShadingGroup'), cm.nt.ObjectSet)
False

この弱点は設計段階から把握された上で、あえてそのようになっています。

何故かというと、 :ref:`gettingstarted-customclasses-nodes` を自由に作れるという仕組みによって、
isinstance でタイプ判別ができるという前提は既に崩れているからです。
pymel も然りです。

そこで、確実にノードタイプを判別するには、
isinstance ではなく、以下のように `~.Node_c.isType` か `~.Node_c.hasFn` メソッドを利用してください。

>>> cm.nt.Node('initialShadingGroup').isType('objectSet')
True
>>> cm.nt.Node('initialShadingGroup').hasFn(api.MFn.kSet)
True

とはいえ、純粋にノードタイプを判別したいという用途ではなく、文字通り、派生クラスのインスタンスかどうかを判別したいのならば
isinstance は有用です。
たとえば、 :ref:`gettingstarted-customclasses-nodes` ではノードタイプ以外の条件も加味してクラスを決定できるため、そういった条件込みで判別したい場合などには有用です。



.. _gettingstarted-plugs:

アトリビュートのラッパークラス
====================================
プラグへのアクセス方法
-------------------------
ノードをラッパーオブジェクトとして扱うと、プラグ（アトリビュート）へのアクセスも便利になります。

以下のように、ノードオブジェクトの属性として、 `.Plug` クラスのオブジェクトを得られます。
`.Plug` は `.Node` と同様に、基底クラス `.CyObject` の派生型です。

ショート名でもロング名でも同じものが得られます。

>>> cmds.file(f=True, new=True)
u'untitled'
>>> cm.nt.Transform()
>>> cm.sel.t
Plug('transform1.t')
>>> cm.sel.translate
Plug('transform1.t')

また、MELコマンドの場合と同様に、
:mayanode:`transform` から :mayanode:`shape` のアトリビュートに直接アクセスもできます。

>>> cm.O('persp').focalLength
Plug('perspShape.fl')

アトリビュート名は、まれに Pythonのキーワードや、ノードオブジェクトのメソッド名などと衝突する場合もあります。
そういった場合のために `~.Node_c.plug` メソッドでもアクセスできます。

>>> cm.sel.plug('t')
Plug('transform1.t')

コンパウンドアトリビュートから子アトリビュートを得ることもできますが、
ノードから直接得ることもできます。

>>> cm.sel.t.tx
Plug('transform1.tx')
>>> cm.sel.tx
Plug('transform1.tx')

しかし、コンパウンドのマルチの場合、いきなり子プラグを得るとインデックスが未解決となってしまいます。

>>> cmds.file(f=True, new=True)
u'untitled'
>>> cmds.polyCube()
[u'pCube1', u'polyCube1']
>>> cmds.select(cm.sel.shape())
>>> cm.sel.gcl
Plug('pCubeShape1.iog[-1].og[-1].gcl')

そういった複雑なケースでは、マルチ要素を解決しながらコンパウンドを下っていけます。

>>> cm.sel.iog[0].og[0].gcl
Plug('pCubeShape1.iog[0].og[0].gcl')

他にも様々な方法でアクセスできます。

>>> cm.sel.plug('iog[0].og[0].gcl')
Plug('pCubeShape1.iog[0].og[0].gcl')
>>> cm.O('pCubeShape1.iog[0].og[0].gcl')
Plug('pCubeShape1.iog[0].og[0].gcl')
>>> cm.O('.iog[0].og[0].gcl')
Plug('pCubeShape1.iog[0].og[0].gcl')


.. _gettingstarted-plugs-value:

値のセットとゲット
-------------------------
`.Plug` クラスにも様々なメソッドがありますが、
たとえば `~.Plug.set` や `~.Plug_c.get` メソッドでは値のセットやゲットができます。

>>> cm.sel.t.get()
[0.0, 0.0, 0.0]
>>> cm.sel.t.set([1, 2, 3])
>>> cm.sel.t.get()
[1.0, 2.0, 3.0]

ここで、ひとつ重要な注意点があります。
それは、単位付きタイプの場合、 `~.Plug.set` や `~.Plug_c.get` では「内部単位」で扱われるという点です。

単位付きタイプには「距離」(doubleLinear)、「角度」(doubleAngle)、「時間」(time) がありますが、
内部単位は、それぞれ Centimeter、Radians、Second となっています。

たとえば、rotate では、通常の人が慣れた Degrees ではなく、以下のように Radians で扱う必要があります。

>>> cm.sel.rx.set(PI * .5)
>>> cm.sel.rx.get()
1.5707963267948966

一見面倒に見えるかもしれませんが、これは「シーン設定（単位）に依存しないプログラミングをすべき」という思想に基づいています。
もし、どうしても「UI設定単位」で扱いたい場合、 `~.Plug.setu` や `~.Plug_c.getu` を用いることもできます。

>>> cm.sel.rx.getu()
90.0
>>> cm.sel.rx.setu(180)
>>> cm.sel.rx.get()
3.141592653589793

ただし、 `~.Plug.setu` や `~.Plug_c.getu` を用いるのは、
スクリプトエディターでちょっとタイプして結果を得るようなインスタントなスクリプトに留めるのが無難です。


.. _gettingstarted-plugs-connection:

コネクション編集
-------------------------
``>>`` や ``<<`` や `~.Plug.connect` メソッドで、プラグの接続ができます。

また、接続を調べるには `.Node` の `~.Node_c.inputs` や `~.Node_c.outputs` 、
`.Plug` の `~.Plug_c.inputs` や `~.Plug_c.outputs` メソッドが利用できます。

>>> cmds.file(f=True, new=True)
>>> a = cm.nt.Transform(n='a')
>>> b = cm.nt.Transform(n='b')
>>> a.t >> b.t
>>> a.t.isSource(), a.t.isDestination()
(True, False)
>>> b.t.isSource(), b.t.isDestination()
(False, True)
>>> b.inputs(asPair=True)
[(Plug('b.t'), Plug('a.t'))]

`~.Plug.connect` メソッドは pymel と指定順序が逆なので注意してください。
これは `~.Plug.disconnect` メソッドと指定順を統一するためです。

そのため、演算子は ``>>`` よりも ``<<`` の利用を推奨します。

>>> b.r.connect(a.r)  # b.r << a.r
>>> b.r.inputs()
[Plug('a.r')]
>>> b.s << a.s
>>> b.s.inputs()
[Plug('a.s')]

切断は ``//`` や `~.Plug.disconnect` メソッドで行えます。

>>> a.t // b.t
>>> b.r.disconnect(a.s)
>>> b.s.disconnect()  # 入力プラグは省略可能

``//`` は pymel と同じく左から右への接続の切断なので `~.Plug.disconnect` メソッドを利用した方が統一感があります。


.. _gettingstarted-plugs-worldspace:

ワールドスペースプラグ
-------------------------
アトリビュートには、ワールドスペースの値を出力するマルチアトリビュートがあります。
それは `~.Plug` の `~.Plug_c.isWorldSpace` が True を返すものです。

たとえば :mayanode:`dagNode` の worldMatrix (wm) や :mayanode:`locator` の worldPosition (wp) など、様々なものがあります。

ワールドスペースプラグのインデックスは、DAGノードインスタンスの番号に依存して決められる必要があります。
インスタンス番号は、DAGノードインスタンスの削除時に自動で欠番が詰められるなど動的に変化するため、
ワールドスペースプラグのインデックスも動的に変化します。
そのため、MELコマンドでは、ワールドスペースプラグをインデックス指定した要素で直接扱うことは推奨されず、
DAGパスと矛盾のないインデックスが Maya によって自動補完されるようになっています。
cymel でもその仕様を踏襲し、ワールドスペースプラグは要素にしないで扱うことを推奨します。

以下は使用例で、ロケータをインスタンスコピーし、その worldPosition をインデックス指定せずに参照しています。

>>> cmds.file(f=True, new=True)
>>> a = cm.nt.Locator(n='a').transform()
>>> b = cm.O(cmds.instance(a)[0])
>>> a.t.set([1, 2, 3])
>>> b.t.set([4, 5, 6])
>>> a.wp.get()
[1.0, 2.0, 3.0]
>>> b.wp.get()
[4.0, 5.0, 6.0]

以下のようにインデックス指定することが、本来のプラグへのアクセスになるのですが、ワールドスペースプラグではそれは推奨されません。

>>> a.wp[0].get()
[1.0, 2.0, 3.0]
>>> b.wp[1].get()
[4.0, 5.0, 6.0]



.. _gettingstarted-command:

コマンドやAPIの併用
====================================
cymelは、pymelのように全てのMayaコマンドのラッパーを提供しません。
また、全てのノードタイプのクラスを提供するものの、APIやコマンドを完全に置き換えるほどの機能は提供しません。
頂点やポリゴンなどのコンポーネントもラップしません。

しかし、ノードやプラグを扱う上での主要な機能は整っているので、それで足りない部分はコマンドやAPIを併用してください。

`.CyObject` を文字列として評価するとその名前になるので、Mayaコマンドの引数にそのまま渡すことができます。

また、コマンドの返す結果を `.O` や `.Os` で受ければ、すぐに `.Node` や `.Plug` として扱えます。

`.CyObject` には、同じものを示す API オブジェクトを得るメソッドがあるので、API を併用する場合に便利です。
`Node.mnode <.Node_c.mnode>` では API2 の :mayaapi2:`MObject` 、
`Node.mpath <.Node_c.mpath>` では API2 の :mayaapi2:`MDagPath` 、
`Plug.mplug <.Plug_c.mplug>` では API2 の :mayaapi2:`MPlug` が得られます。
また、
`Node.mnode1 <.Node_c.mnode1>` では API1 の :mayaapi1:`MObject` 、
`Node.mpath1 <.Node_c.mpath1>` では API1 の :mayaapi1:`MDagPath` 、
`Plug.mplug1 <.Plug_c.mplug1>` では API1 の :mayaapi1:`MPlug` が得られます。

さらに、
`.CyObject` のオブジェクトを得る際には、名前だけでなく、
API2 の :mayaapi2:`MObject` 、 :mayaapi2:`MDagPath` 、 :mayaapi2:`MPlug` を指定することもできます
（API1 のそれらはサポートされていません）。



.. _gettingstarted-datatypes:

データタイプクラス
====================================
クラスの種類
-------------------------
cymelは以下の数学クラスを提供します。カッコ内は別名です。

- :ref:`gettingstarted-datatypes-boundingbox` (`.BB`)  ... バウンディングボックス
- :ref:`gettingstarted-datatypes-vector` (`.V`)  ... 3次元ベクトル
- :ref:`gettingstarted-datatypes-matrix` (`.M`)  ... 4x4行列
- :ref:`gettingstarted-datatypes-quaternion` (`.Q`)  ... クォータニオン
- :ref:`gettingstarted-datatypes-eulerrotation` (`.E`)  ... オイラー角回転
- :ref:`gettingstarted-datatypes-transformation` (`.X`)  ... トランスフォーメーション情報

それらの中には `.Plug` の値として直接セットしたり、直接ゲットしたりすることができるものもあります。

また、異なる型同士の変換操作もサポートされています。


.. _gettingstarted-datatypes-boundingbox:

BoundigBox
-------------------------
`.BoundingBox` (`.BB`) はバウンディングボックスクラスで、Maya API の :mayaapi2:`MBoundingBox` に相当します。

`.DagNode` の `~.DagNodeMixin.boundingBox` メソッドで取得できます。

`.BoundingBox` の保持する位置情報には `.Vector` が利用されています。


.. _gettingstarted-datatypes-vector:

Vector
-------------------------
`.Vector` (`.V`) は3次元ベクトルクラスで、
Maya API の :mayaapi2:`MPoint` と :mayaapi2:`MVector` に相当します。
API では、位置を表すか方向を表すかで2種類を使いわける必要がありますが、cymelでは `.Vector` のみに統一されています。

`.Vector` は :mayaapi2:`MPoint` と同じく同次座標表現が可能な w を持っていますが、
デフォルトの 1.0 である限りは隠蔽され、ほとんど意識する必要はありません。
また、方向ベクトルとして扱う場合も 0.0 にする必要はなく、メソッドの種類に応じて適切に扱われます。

たとえば、
``*`` 演算子か `~.Vector.dot` メソッドで、3次元ベクトルの内積を計算しますが、
`.Vector.dot4` メソッドは4次元ベクトルの内積です。
また、 `~.Vector.dot4r` メソッドは、ベクトルが4x1行列と1x4行列であるものとして、行列の積を計算します。

>>> cm.V(1, 2, 3) * cm.V(4, 5, 6)
32.0
>>> cm.V(1, 2, 3).dot(cm.V(4, 5, 6))
32.0
>>> cm.V(1, 2, 3).dot4(cm.V(4, 5, 6))
33.0
>>> cm.V(1, 2, 3).dot4r(cm.V(4, 5, 6))
Matrix(((4, 5, 6, 1), (8, 10, 12, 2), (12, 15, 18, 3), (4, 5, 6, 1)))

また、 ``^`` 演算子か `~.Vector.cross` メソッドでは、3次元ベクトルの外積を計算します。

>>> cm.V(1, 2, 3) ^ cm.V(4, 5, 6)
Vector(-3.000000, 6.000000, -3.000000)
>>> cm.V(1, 2, 3).cross(cm.V(4, 5, 6))
Vector(-3.000000, 6.000000, -3.000000)

他にも様々なメソッドがありますので、ドキュメントを参照してください。

`.Vector` は w を持っていますが、それがデフォルトの 1.0 である限り、長さ 3 のシーケンスとして振る舞います。
よって、4次元ベクトル値としては扱いにくいですが、3次元ベクトル値としては扱いやすいものになっています。

たとえば、double3型アトリビュートの値に直接セットすることができます。
ゲットで得られるのは `list` ですが、そこからすぐに `.Vector` にすることもできます。

>>> v = cm.V(1, 2, 3)
>>> cm.nt.Transform()
>>> cm.sel.t.set(v)
>>> v + cm.V(cm.sel.t.get())
Vector(2.000000, 4.000000, 6.000000)


.. _gettingstarted-datatypes-matrix:

Matrix
-------------------------
`.Matrix` (`.M`) は4x4行列クラスで、Maya API の :mayaapi2:`MMatrix` に相当します。

matrix型アトリビュートのゲットやセットや `.DagNode` の `~.DagNodeMixin.getM` や `~.TransformMixin.setM` で直接サポートされます。

以下は、ローカルマトリックスを取得する例です。
プラグから得ることでも `~.DagNodeMixin.getM` を使用することでも、同じものが得られます。

>>> cmds.file(f=True, new=True)
>>> a = cm.nt.Transform(n='a')
>>> a.t.set((1, 2, 3))
>>> a.r.setu((10, 20, 30))
>>> a.s.set((1.2, 1.4, 1.6))
>>> a.m.get()
Matrix(((0.976557, 0.563816, -0.410424, 0), (-0.617357, 1.23559, 0.228446, 0), (0.605636, 0.0288453, 1.48067, 0), (1, 2, 3, 1)))
>>> a.getM()
Matrix(((0.976557, 0.563816, -0.410424, 0), (-0.617357, 1.23559, 0.228446, 0), (0.605636, 0.0288453, 1.48067, 0), (1, 2, 3, 1)))

以下は、ワールドマトリックスを取得する例です。
`既に説明済み`__ ですが、 wm にはインデックスを指定しないことが推奨されます。

__ #gettingstarted-plugs-worldspace

>>> b = cm.nt.Transform(n='b', p=a)
>>> b.t.set((4, 5, 6))
>>> b.r.set((-10, -20, -30))
>>> b.wm.get()
Matrix(((0.365467, 0.560012, 1.41804, 0), (1.25209, -0.335616, -0.121765, 0), (0.0174783, 1.19128, -0.622367, 0), (5.45326, 10.6063, 11.3845, 1)))
>>> b.getM(ws=True)
Matrix(((0.365467, 0.560012, 1.41804, 0), (1.25209, -0.335616, -0.121765, 0), (0.0174783, 1.19128, -0.622367, 0), (5.45326, 10.6063, 11.3845, 1)))

以下は `~.TransformMixin.setM` の使用例です。

>>> c = cm.nt.Transform(n='c')
>>> c.setM(b.getM(ws=True))
>>> c.m.get()
Matrix(((0.365467, 0.560012, 1.41804, 0), (1.25209, -0.335616, -0.121765, 0), (0.0174783, 1.19128, -0.622367, 0), (5.45326, 10.6063, 11.3845, 1)))

``*`` 演算子で `.Matrix` 同士の積を計算できます。

>>> b.m.get() * a.m.get()
Matrix(((0.365467, 0.560012, 1.41804, 0), (1.25209, -0.335616, -0.121765, 0), (0.0174783, 1.19128, -0.622367, 0), (5.45326, 10.6063, 11.3845, 1)))

`.Vector` に `.Matrix` を乗じるか `~.Vector.xform4` メソッドで、位置座標を変換できます。

>>> m = c.getM()
>>> cm.V(1, 2, 3) * m
Vector(8.375328, 14.068906, 10.691944)
>>> cm.V(1, 2, 3).xform4(m)
Vector(8.375328, 14.068906, 10.691944)

また、方向ベクトルを変換するには `~.Vetor.xform3` メソッドを使用します。
それは w が 0.0 の場合に似ていますが、 `~.Vector.xform3` を用いれば w はデフォルトの 1.0 のままです。

>>> cm.V(1, 2, 3, 0) * m
Vector(2.922072, 3.462623, -0.692589, 0.000000)
>>> cm.V(1, 2, 3).xform3(m)
Vector(2.922072, 3.462623, -0.692589)

`.Matrix` を他の型に変換する操作もサポートされています。

平行移動値を取り出す `~.Matrix.asTM` や `~.Matrix.asT` 、
回転を取り出す `~.Matrix.asRM` や `~.Matrix.asQ` や `~.Matrix.asE` や `~.Matrix.asD` 、
スケールやシアーを取り出す `~.Matrix.asSM` や `~.Matrix.asS` や `~.Matrix.asSh` 、
全部まとめて分解（ `.Transformation` を得る）する `~.Matrix.asX` などがあります。


.. _gettingstarted-datatypes-quaternion:

Quaternion
-------------------------
`.Quaternion` (`.Q`) はクォータニオンクラスで、Maya API の :mayaapi2:`MQuaternion` に相当します。

長さ 4 のシーケンスとしても振る舞います。

ノードの `~.DagNodeMixin.getQ` メソッドで、ノードの回転値を `.Quaternion` で得ることができます。

以下のコードは :ref:`gettingstarted-datatypes-matrix` で説明した例の続きで、
`~.DagNodeMixin.getQ` の使用例です。

>>> a.getQ()
Quaternion(0.0381346, 0.189308, 0.239298, 0.951549)
>>> a.getQ(ws=True)
Quaternion(0.0381346, 0.189308, 0.239298, 0.951549)
>>> b.getQ()
Quaternion(-0.711601, -0.405992, -0.551087, 0.158423)
>>> b.getQ(ws=True)
Quaternion(-0.691413, -0.473257, -0.399343, 0.372158)

`~.DagNodeMixin.getQ` は、デフォルトでは rotateAxis を含まない回転を得られます（jointOrient や ws=True による上位の変換は含まれます）。
`~.DagNodeMixin.getJOQ` では、rotate を含まない回転（jointOrient まで）を得られます。
さきほどの例は、 :mayanode:`transform` ノードなので jointOrient を持たないため、親で `~.DagNodeMixin.getQ` することと等しくなります。

>>> b.getJOQ(ws=True)
Quaternion(0.0381346, 0.189308, 0.239298, 0.951549)

``*`` 演算子でクォータニオン同士の積を計算できます。

>>> b.getQ() * a.getQ()
Quaternion(-0.678253, -0.5056, -0.367246, 0.386616)

上記で b と a のローカルクォータニオンの積が b のワールドクォータニオンと等しくならないのは、a が非一様 scale を持っているからです。
a の scale を初期化すれば等しくなります。

>>> a.s.set((1, 1, 1))
>>> b.getQ(ws=True)
Quaternion(-0.678253, -0.5056, -0.367246, 0.386616)

回転情報を扱う他の型との変換操作もサポートされています。

`.Matrix` とは、その `~.Matrix.asQ` と `.Quaternion` の `~.Quaternion.asM` とで相互に変換ができます。
また、
`.EulerRotation` とは、その `~.EulerRotation.asQ` と `.Quaternion` の `~.Quaternion.asE` とで相互に変換ができます。
`~.Quaternion.asD` では、オイラー角回転を Degrees で得られます。
さらに、 `~.Quaternion.asX` では `.Transformation` 型に変換できます。


.. _gettingstarted-datatypes-eulerrotation:

EulerRotation
-------------------------
`.EulerRotation` (`.E`) はオイラー角回転クラスで、Maya API の :mayaapi2:`MEulerRotation` に相当します。

rotateOrder も持っていますが、単なる長さ 3 のシーケンスとしても振る舞いますので、
オイラー角回転値を持つ rotate 、 rotateAxis 、 jointOrient などのアトリビュートのセットやゲットに便利です。

>>> cm.E(a.r.get(), a.ro.get())
EulerRotation(0.174533, 0.349066, 0.523599, XYZ)
>>> a.getQ(jo=False).asE()
EulerRotation(0.174533, 0.349066, 0.523599, XYZ)

`.degrot` 関数によって、Degrees 単位の値から取得することもできます。

>>> cm.degrot(10, 20, 30)
EulerRotation(0.174533, 0.349066, 0.523599, XYZ)

回転情報を扱う他の型との変換操作もサポートされています。

`.Matrix` とは、その `~.Matrix.asE` と `.EulerRotation` の `~.EulerRotation.asM` とで相互に変換ができます。
また、
`.Quaternion` とは、その `~.Quaternion.asE` と `.EulerRotation` の `~.EulerRotation.asQ` とで相互に変換ができます。
`~.EulerRotation.asD` では、オイラー角回転を Degrees で得られます。
さらに、 `~.EulerRotation.asX` では `.Transformation` 型に変換できます。


.. _gettingstarted-datatypes-transformation:

Transformation
-------------------------
`.Transformation` (`.X`) はトランスフォーメーション情報クラスで、
Maya API の :mayaapi2:`MTransformationMatrix` に似ていますが、もっと洗練されています。

Mayaのmatrix型アトリビュートは、単なる「マトリックス」か「トランスフォーメーション情報」かの2種類の形式で情報を持てるようになっています。
cymelのクラスでいうと `.Matrix` か `.Transformation` です。

そして、 `~.Transformation` は、
:mayanode:`transform` ノードと :mayanode:`joint` ノードのローカルマトリックスに影響を与えるアトリビュートを
オブジェクト属性として扱えるようにしつつ、`.Matrix` の合成・分解操作をサポートします。

トランスフォーメーションを `.Matrix` として扱うと、元のアトリビュート値は維持されませんが
（translate、rotate、scale、shearには分解できますが、ピボットや複数の回転アトリビュートなどの元の状態の完全な復元はできません）、
`.Transformation` として扱えば、アトリビュートの状態を完全に保持できます。

なお、2020から追加された offsetParentMatrix はローカルマトリックスには含まれず parentMatrix に含まれる扱いとなるため、
`.Transformation` のオブジェクト属性としてはサポートされません。

では、その働きを見るために、まず、ノードを1つ作り、アトリビュートを細かく設定します。

>>> cmds.file(f=True, new=True)
>>> a = cm.nt.Transform(n='a')
>>> a.t.set((1, 2, 3))
>>> a.rp.set((2, 3, 4))
>>> a.r.setu((10, 20, 30))
>>> a.ro.set(YXZ)
>>> a.ra.setu((3, 6, 9))
>>> a.sp.set((5, 6, 7))
>>> a.s.set((1.2, 1.4, 1.6))

translate、rotate、scale だけでなく rotateOrder や rotateAxis 、ピボットなども設定しました。

そして、アトリビュート m と xm をゲットした結果を比べてみます。

>>> a.m.get()
Matrix(((0.784932, 0.76995, -0.480686, 0), (-0.818564, 1.07082, 0.378546, 0), (0.767799, 0.091752, 1.40074, 0), (0.260018, -1.52541, -0.437171, 1))) 
>>> a.xm.get()
Transformation(rp=Vector(2.000000, 3.000000, 4.000000), sp=Vector(5.000000, 6.000000, 7.000000), sh=Vector(0.000000, 0.000000, 0.000000), s=Vector(1.200000, 1.400000, 1.600000), r=EulerRotation(0.185486, 0.343542, 0.586718, XYZ), ra=Quaternion(0.0219557, 0.0542077, 0.0769589, 0.995317), t=Vector(1.000000, 2.000000, 3.000000))

m も xm も同じmatrix型アトリビュートですが、m には単なるマトリックスが出力され、xm にはトランスフォーメーション情報が出力されています。
そして、cymel はそれらをそのまま取得できます。

トランスフォーメーション情報を持っているアトリビュートでも単なるマトリックスとして評価することもできます（ :mayanode:`getAttr` コマンドではそうなります）。
その場合は、明示的に `~.Plug_c.getM` メソッドを使うか、得られた `.Transformation` の属性 ``m`` を参照します。

>>> a.xm.getM()
Matrix(((0.784932, 0.76995, -0.480686, 0), (-0.818564, 1.07082, 0.378546, 0), (0.767799, 0.091752, 1.40074, 0), (0.260018, -1.52541, -0.437171, 1))) 
>>> a.xm.get().m
Matrix(((0.784932, 0.76995, -0.480686, 0), (-0.818564, 1.07082, 0.378546, 0), (0.767799, 0.091752, 1.40074, 0), (0.260018, -1.52541, -0.437171, 1))) 

ノードから `.Transformation` を得るには `~.DagNodeMixin.getX` メソッドも利用できます。
xm アトリビュートからゲットすることと等しいですが、 `~.DagNodeMixin.getX` ではワールドスペースの値を得ることもできます。

>>> b = cm.nt.Transform(n='b', p=a)
>>> b.t.set((4, 5, 6))
>>> b.r.set((-10, -20, -30))
>>> b.xm.get()
Transformation(s=Vector(1.000000, 1.000000, 1.000000), sh=Vector(0.000000, 0.000000, 0.000000), r=EulerRotation(-10, -20, -30, XYZ), t=Vector(4.000000, 5.000000, 6.000000))
>>> b.getX()
Transformation(s=Vector(1.000000, 1.000000, 1.000000), sh=Vector(0.000000, 0.000000, 0.000000), r=EulerRotation(-10, -20, -30, XYZ), t=Vector(4.000000, 5.000000, 6.000000))
>>> b.getX(ws=True)
Transformation(q=Quaternion(-0.651708, -0.507318, -0.329514, 0.457521), s=Vector(1.567808, 1.300522, 1.318314), sh=Vector(0.047563, -0.101130, -0.171420), t=Vector(3.913720, 7.459003, 7.937241))

一方、`.Transformation` 情報をセットするには `~.TransformMixin.setX` メソッドが便利です。
それは `.Transformation` が持っている全ての属性値を、
:mayanode:`transform` や :mayanode:`joint` ノードのプラグに、そのままセットすることに相当します。

たとえば、以下に示すように `~.TransformMixin.setM` メソッドではマトリックスを完全に一致させることができますが、個々のプラグ値までは一致しません。

>>> c = cm.nt.Transform(n='c')
>>> c.setM(a.getM())
>>> c.m.get().isEquivalent(a.m.get())
True
>>> cm.V(c.t.get()).isEquivalent(cm.V(a.t.get()))
False
>>> cm.V(c.rp.get()).isEquivalent(cm.V(a.rp.get()))
False
>>> cm.V(c.r.get()).isEquivalent(cm.V(a.r.get()))
False
>>> c.ro.get() == a.ro.get()
False
>>> cm.E(c.ra.get()).asQ().isEquivalent(cm.E(a.ra.get()).asQ())
False
>>> cm.V(c.sp.get()).isEquivalent(cm.V(a.sp.get()))
False
>>> cm.V(c.s.get()).isEquivalent(cm.V(a.s.get()))
True

しかし、 `~.TransformMixin.setX` では、プラグ値を全て一致させることができます。
プラグ値の完全なコピーができるので、個々の値に誤差もないため、この例では単純に == で比較しています。

>>> c.setX(a.getX())
>>> c.m.get() == a.m.get()
True
>>> c.t.get() == a.t.get()
True
>>> c.rp.get() == a.rp.get()
True
>>> c.r.get() == a.r.get()
True
>>> c.ro.get() == a.ro.get()
True
>>> c.ra.get() == a.ra.get()
True
>>> c.sp.get() == a.sp.get()
True
>>> c.s.get() == a.s.get()
True

:mayanode:`joint` ノードと :mayanode:`transform` ノードのように、使用できるアトリビュートが異なるノード間でも `.Transformation` をコピーできます。
:mayanode:`joint` には jointOrient や inverseScale などの :mayanode:`transform` には無いアトリビュートが追加されている一方、ピボットは変更できません。
shear は隠されていますが変更可能です（Maya 2019 から 2020.0 まで shear が変更できない問題がありましたが修正されました）。

以下の例では、これまでと同じ `.Transformation` を :mayanode:`joint` ノードにセットしています。
ピボットは変更せずに維持しされつつ、マトリックスが一致するように translate 値が調整されているのを確認できます。

>>> d = cm.nt.Joint(n='d')
>>> d.setX(a.getX())
>>> d.m.get().isEquivalent(a.m.get())
True
>>> cm.V(d.t.get()).isEquivalent(cm.V(a.t.get()))
False
>>> cm.V(d.rp.get()).isEquivalent(cm.V(a.rp.get()))
False
>>> cm.V(d.r.get()).isEquivalent(cm.V(a.r.get()))
True
>>> d.ro.get() == a.ro.get()
True
>>> cm.E(d.ra.get()).asQ().isEquivalent(cm.E(a.ra.get()).asQ())
True
>>> cm.V(d.sp.get()).isEquivalent(cm.V(a.sp.get()))
False
>>> cm.V(d.s.get()).isEquivalent(cm.V(a.s.get()))
True


.. _gettingstarted-datatypes-matrixdecomposition:

Transformation を利用した Matrix の分解
-----------------------------------------
これまでの例では `.Transformation` をノードから取得しましたが、もちろん、単なる値として生成することもできます。

たとえば、以下のようにコンストラクタに属性値を指定して生成できます。

>>> cm.X(r=cm.degrot(10, 20, 30, YXZ), t=(1, 2, 3))
Transformation(r=EulerRotation(0.174533, 0.349066, 0.523599, YXZ), t=Vector(1.000000, 2.000000, 3.000000))

回転情報は `.EulerRotation` ではなく `.Quaternion` で指定することもできます。
以下は最初に内部的に設定される値が `.Quaternion` になっていますが、結局同じ `.Transformation` を生成していることになります。

>>> cm.X(q=cm.degrot(10, 20, 30, YXZ).asQ(), ro=YXZ, t=(1, 2, 3))
Transformation(q=Quaternion(0.0381346, 0.189308, 0.268536, 0.943714), ro=4, t=Vector(1.000000, 2.000000, 3.000000))

また、コンストラクタには `.Matrix` をそのまま渡せます。

それは `~.Matrix.asX` メソッドを使用することと同じです
（割愛しますが、属性名を指定せずに `.EulerRotation` や `.Quaternion` をそのまま指定することも同様に可能です）。

以下の例では、 `~.Matrix` から `.Transformation` を得るとともに、その属性値を参照しています。

>>> r = cm.degrot(10, 20, 30, YXZ)
>>> m = r.asM() * cm.M.makeT((1, 2, 3))
>>> cm.X(m)
Transformation(q=Quaternion(0.0381346, 0.189308, 0.268536, 0.943714), s=Vector(1.000000, 1.000000, 1.000000), sh=Vector(0.000000, 0.000000, 0.000000), t=Vector(1.000000, 2.000000, 3.000000))
>>> m.asX()
Transformation(q=Quaternion(0.0381346, 0.189308, 0.268536, 0.943714), s=Vector(1.000000, 1.000000, 1.000000), sh=Vector(0.000000, 0.000000, 0.000000), t=Vector(1.000000, 2.000000, 3.000000))
>>> x = m.asX()
>>> x.t
Vector(1.000000, 2.000000, 3.000000)
>>> x.r
EulerRotation(0.185486, 0.343542, 0.586718, XYZ)

得られた `.Transformation` から q や r や s や sh や t などの値を得ることができますので、
この操作はマトリックスをトランスフォーメーション要素に分解することと等しいわけです。

さらに、進んだ操作として、ピボットなどの補助属性を条件として設定した上で、マトリックスを分解することもできます。

>>> x = cm.X()
>>> x.rp = cm.V(2, 4, 6)
>>> x.jo = cm.degrot(5, 10, 15).asQ()
>>> x.ro = ZYX
>>> x.sp = cm.V(1, 2, 3)
>>> x.m = m
>>> x.t
Vector(0.865305, 2.632209, 2.573444)
>>> x.r
EulerRotation(-0.0165951, 0.207732, 0.291455, ZYX)
>>> x.q
Quaternion(0.00688977, 0.103775, 0.143573, 0.984159)
>>> x.s
Vector(1.000000, 1.000000, 1.000000)
>>> x.sh
Vector(0.000000, 0.000000, 0.000000)

上記の例では、最初にピボットや jointOrient などを設定し（コンストラクタの引数で指定することもできます）、最後に matrix を代入しています。
そして、補助属性とマトリックスから逆算される t と r (または q ) と s と sh が分解されているのです。



.. _gettingstarted-datatypes-attr:

アトリビュートとデータタイプのさらなる使用例
--------------------------------------------------
`.Transformation` の例で使用した m や xm などのアトリビュートは出力専用アトリビュートでしたので、
ダイナミックアトリビュートを使って、もう少し試してみましょう。

`.Node` の `~.Node.addAttr` メソッドは :mayacmd:`addAttr` コマンドを簡単に使用できるようにしたラッパーです。

たとえば、double3 型アトリビュートの追加も、以下のように簡単です。

>>> cmds.file(f=True, new=True)
>>> a = cm.nt.Transform(n='a')
>>> a.addAttr('testrot', 'double3', 'doubleAngle', cb=True)

それでは、matrix型アトリビュートを追加してみます。

>>> a.addAttr('foo', 'matrix')
>>> a.foo.get()

追加したアトリビュートの初期値は値を返しません（None）。
データ型アトリビュートの初期値は null だからです。

以下のように、 `.Matrix` をセットすれば、その値を返すようになります。

>>> a.foo.set(cm.M())
>>> a.foo.get()
Matrix(((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))

または、 `.Transformation` をセットしても同様です。

>>> a.foo.set(cm.X())
>>> a.foo.get()
Transformation(s=Vector(1.000000, 1.000000, 1.000000), sh=Vector(0.000000, 0.000000, 0.000000), r=EulerRotation(0, 0, 0, XYZ), t=Vector(0.000000, 0.000000, 0.000000))

matrix型は、どちらの形式でも値を保持できます。

`.Plug` は本来のコマンドでは不可能な `~.Plug.reset` メソッドも持っています（もちろん undo も可能です）。
初期値は null でしたので、リセットすると null に戻ります（Python では None）。

>>> a.foo.reset()
>>> a.foo.get()

そして、実は、 `~.Node.addAttr` の際にデフォルト値を指定することもできます。

本来のコマンドでは、デフォルト値の指定は数値型のアトリビュートでしかサポートされていませんが、cymel なら可能です（もちろん undo も可能です）。

以下の例では、デフォルト値に `.Transformation` を指定したアトリビュートを追加しています。

>>> a.addAttr('bar', 'matrix', dv=cm.X())
>>> a.bar.get()
Transformation(s=Vector(1.000000, 1.000000, 1.000000), sh=Vector(0.000000, 0.000000, 0.000000), r=EulerRotation(0, 0, 0, XYZ), t=Vector(0.000000, 0.000000, 0.000000))
>>> a.bar.set(cm.M())
>>> a.bar.get()
Matrix(((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
>>> a.bar.reset()
>>> a.bar.get()
Transformation(s=Vector(1.000000, 1.000000, 1.000000), sh=Vector(0.000000, 0.000000, 0.000000), r=EulerRotation(0, 0, 0, XYZ), t=Vector(0.000000, 0.000000, 0.000000))



.. _gettingstarted-customclasses:

カスタムクラス
====================================
cymel では、標準で備わっているノードやプラグのクラスを継承した独自のクラスを使用することができます。


.. _gettingstarted-customclasses-nodes:

カスタムノードクラス
-------------------------------------------
独自のノードクラスを使用する最も簡単な方法は、そのノードタイプに対応する標準のクラスを継承したクラスを実装し、使用する際はただそれを明示することです。

次のコードでは、標準の `.Transform` クラスを継承した ``MyTransform`` クラスを作っています。

.. code-block:: python

    class MyTransform(cm.nt.Transform):
        def clearRestPose(self):
            self.mfn().clearRestPosition()

        def saveRestPose(self):
            self.mfn().setRestPosition(self.mfn().transformation())

        def gotoRestPose(self):
            mfn = self.mfn()
            r = mfn.restPosition()
            u = mfn.transformation()
            setx = mfn.setTransformation
            cm.docmd(lambda: setx(r), lambda: setx(u))

Maya API の :mayaapi2:`MFnTransformation` クラスの持つ Rest Position 機能を利用して、現在のポーズを一時的に保存したり、その状態に戻ったりするメソッドを実装しています。APIのこの機能は、Maya内部では使用されず、シーンファイルにも保存されない、APIレベルの一時的なキャッシュです。
APIでの操作となると通常はアンドゥはできませんが、この実装では cymel の `.docmd` を使用してアンドゥにも対応させています。

以下はこのクラスの使用例です。

>>> cmds.polyCube()
>>> obj = MyTransform(cmds.ls(sl=True)[0])
>>> obj.t.set((1, 2, 3))
>>> obj.r.setu((10, 20, 30))
>>> obj.s.set((2, 4, 6))
>>> obj.saveRestPose()
>>> obj.t.reset()
>>> obj.r.reset()
>>> obj.s.reset()
>>> obj.gotoRestPose()
>>> cmds.undo()
# Undo: obj.gotoRestPose() # 
>>> cmds.redo()
# Redo: obj.gotoRestPose() #

この例では、実装した ``MyTransform`` クラスを明示してインスタンスを得る必要があります。 `.sel` や `.selected` でカレントセレクションから得たり、親や子の :mayanode:`transform` やコネクションを辿って得られるオブジェジェクトでは通常の `.Transform` クラスが使用されてしまい ``MyTransform`` クラスが使用されることはありません。



.. _gettingstarted-customclasses-registration:

検査メソッド付きノードクラスの登録
-------------------------------------------
カスタムクラスを明示せずにそのインスタンスを得られるようにするには、そのクラスを `.NodeTypes` (別名: `cm.nt` ) に登録する必要があります。登録するには `.NodeTypes.registerNodeClass` を使用します。

早速 ``MyTransform`` クラスを登録してみましょう、といきたいところですが、このクラスは :mayanode:`transform` ノードタイプに対応する標準の `.Transform` クラスを継承したものなので、そのまま登録しようとすると :mayanode:`transform` に対応するクラスが2つになってしまい、その使い分けをどうするかが問題になります。

この問題を解決するには、同じ :mayanode:`transform` タイプでも ``MyTransform`` を利用すべきかどうでないかを判別するためのタグ情報をノードに実際に追加するようにします。どのようなタグにするかは完全に自由ですが、シーンファイルに保存されることが望ましいので、カスタムアトリビュートを使用することが一般的です。

クラスでタグを識別する仕組みと、ノードを新規に作成した際にタグを追加する仕組みは、cymel のクラスでサポートされているので、さきほどの ``MyTransform`` クラスに、次の2つのメソッドを追加実装します（これらのメソッドは cyeml のクラスタシステムで決められているルールです）。

.. code-block:: python

    class MyTransform(cm.nt.Transform):
        @staticmethod
        def _verifyNode(mfn, name):
            return mfn.hasAttribute('myNodeTag')

        @classmethod
        def createNode(cls, **kwargs):
            nodename = super(MyTransform, cls).createNode(**kwargs)
            cmds.addAttr(nodename, ln='myNodeTag', at='message', h=True)
            return nodename

        # (実装済みのメソッドが続きます)

    cm.nt.registerNodeClass(MyTransform, 'transform')

絶対に必要なのは検査メソッド `_verifyNode <.NodeTypes.registerNodeClass>` のみで、生成メソッド `~.Node_c.createNode` は実装が推奨されているくらいの位置付けです。

最後に `~.NodeTypes.registerNodeClass` を呼び出して、クラスを cymel に登録しています。第二引数には、紐付けるノードタイプ名を指定します。

もし、検査メソッド ``_verifyNode`` を実装していない ``MyTransform`` クラスを登録しようとすると、ノードタイプの継承関係と完全に一致しないという理由でエラーになります（Maya の :mayanode:`transform` の親タイプは :mayanode:`dagNode` なので、クラスでも `.DagNode` を直接継承しなければならないため）。

一方、検査メソッド付きのクラスでは、ノードタイプとの関連付けは厳格でなくても良いので、紐付けるノードタイプは、矛盾さえなければ割と自由に指定できます。たとえば、 :mayanode:`transform` の代わりに :mayanode:`dagNode` や :mayanode:`node` などを指定して、広範囲のノードタイプに対応させることもできます（その場合は、継承するクラスも `.DagNode` や `.Node` にすべきですし、この例で実装した機能は :mayaapi2:`MFnTransform` の機能を利用したものなので無理がありますが）。
また、 `~.NodeTypes.registerNodeClass` を複数回呼び出して、継承関係の無い複数のノードタイプに紐付けることさえできます。

cymel の通常の使用方法として、ノードクラスのインスタンスを得る際に既存の名前を指定しなければ `~.Node_c.createNode` が発動します。
次のように使用できます。

>>> MyTransform()
# Result: MyTransform('myTransform1') # 
>>> MyTransform(n='foo')
# Result: MyTransform('foo') # 

このように作成したノードは、識別タグ（カスタムアトリビュート）が設定されているので、 `.sel` などで普通に得ることができます。

>>> cm.sel
# Result: MyTransform('foo') # 

しかし、先ほどの例のように作成済みのキューブなどには利用できないので、既存の :mayanode:`transform` にもタグのアトリビュートを追加するメソッドを追加すれば良いです。そのやり方は完全に自由で、システムでも何もサポートされていません。ここでは、次のように ``addClassTag`` クラスメソッドを追加し、先ほどの `~.Node_c.createNode` メソッドでもそれを呼ぶように変更します。 ``_verifyNode`` やその他のメソッドはそのままです。

.. code-block:: python

    class MyTransform(cm.nt.Transform):
        @classmethod
        def createNode(cls, **kwargs):
            nodename = super(MyTransform, cls).createNode(**kwargs)
            cls.addClassTag(nodename)
            return nodename

        @classmethod
        def addClassTag(cls, nodename):
            cmds.addAttr(nodename, ln='myNodeTag', at='message', h=True)

        # (実装済みのメソッドが続きます)

これで以下のようにして既存 :mayanode:`transform` にもタグを追加することで、 ``MyTransform`` が使用されるようにできます。

>>> MyTransform.addClassTag(cmds.polyCube()[0])
>>> cm.sel
# Result: MyTransform('pCube1') # 



.. _gettingstarted-customclasses-basic-registration:

ベーシックノードクラスの登録
-------------------------------------------
先ほどの ``MyTransform`` は、標準のクラス `.Transform` が在った上で、それに機能追加したクラスを実装していました。
しかし、標準のクラスを完全に乗っ取ってしまいたいこともあります。

実際は、標準のクラスを乗っ取るというより、標準だと何の機能も実装されていないノードタイプのクラスを自前で実装したいことがあります。

cymel では全てのノードタイプに対応したクラスが提供されますが、本当に機能が実装されたクラスはごくわずかで、ほとんどのものは自動生成されるクラスでノードタイプ階層をクラス階層にマップする意義くらいしかありません。
全てのノードタイプクラスは `cm.nt <.NodeTypes>` で提供されますが、標準で機能が実装されていないクラスは最初にアクセスした際に自動生成されます。それは、クラスの出自を確認することで判別できます。

>>> cm.nt.DagNode
# Result: <class 'cymel.core.cyobjects.dagnode.DagNode'> # 
>>> cm.nt.Transform
# Result: <class 'cymel.core.cyobjects.transform.Transform'> # 
>>> cm.nt.Shape
# Result: <class 'cymel.core.cyobjects.shape.Shape'> # 
>>> cm.nt.Joint
# Result: <class 'cymel.core.typeregistry.Joint'> # 
>>> cm.nt.ObjectSet
# Result: <class 'cymel.core.typeregistry.ObjectSet'> # 

`cymel.core.typeregistry` に在るのが自動生成されたクラスです。上記の例では `Joint` と `ObjectSet` がそれにあたります。それらは、ただそのノードタイプに対応したクラスがあるだけで、特別な機能は何も持っていません。
もちろん、プラグインで追加したノードタイプに対応するクラスも自動生成されますが、当然、何も特別な機能は持ちません。

それらを自分で実装してしまっても良いでしょう。

ノードタイプに一対一で対応させる場合は、検査メソッド ``_verifyNode`` や生成メソッド `~.Node_c.createNode` は不要です。ただ `~.NodeTypes.registerNodeClass` するだけです。
ただし、クラス階層が実際のノードタイプ階層と完全に一致している必要があるので、クラスの継承は正確に指定する必要があります。自動で解決されるように記述するには `~.NodeTypes.parentBasicNodeClass` メソッドの使用が便利です。

次の例は :mayanode:`objectSet` タイプに対応するクラスの実装例です（あくまでも簡易的な実装で、あまり深くは考えていません）。

.. code-block:: python

    class ObjectSet(cm.nt.parentBasicNodeClass('objectSet')):
        def __contains__(self, item):
            return cmds.sets(item, im=self.name())

        def __len__(self):
            return cmds.sets(self.name(), q=True, s=True)

        def __getitem__(self, i):
            return cm.O(cmds.sets(self.name(), q=True, no=True)[i])

        def add(self, *items):
            cmds.sets(*items, add=self.name())

        def remove(self, *items):
            cmds.sets(*items, rm=self.name())

    cm.nt.registerNodeClass(ObjectSet, 'objectSet')

もし、そのノードタイプに対してクラスが既に生成されていたら次のような警告が出力された上で上書き登録されます。

.. code-block:: python

    # Warning: node class deregistered: <class 'cymel.core.typeregistry.ObjectSet'> # 

そのクラスを継承しているクラスが存在するならいったん全て登録抹消されます。それらのノードタイプのクラスも次に評価された際に再生成されますが、生成済みのインスタンスは登録抹消されたクラスのままとなるので気をつけてください。このようなことから、クラスの登録は Maya 起動後の早い段階でやるのが望ましいといえます。



.. _gettingstarted-customclasses-plugs:

カスタムプラグクラス
-------------------------------------------
(工事中)



.. _gettingstarted-utilities:

ユーティリティ
====================================
(工事中)



.. _gettingstarted-uicontrols:

UIコントロールクラス
====================================
cymel は、MELの全てのUIコントロールをラップしたクラスを提供します。

各クラス名は、MELコマンド名の先頭を大文字にした名前になります。
たとえば :mayacmd:`window` なら `.Window` という具合です。

pymel にとてもよく似ていて、大きな進化はしていません（たとえば with が少し使いやすくなっていたりしますが）。
使い方もほとんど同じです。

以下に簡単な使用例を示します。

.. code-block:: python

    import cymel.ui as cmu
    with cmu.Window() as wnd:
        with cmu.AutoLayout():
            cmu.Button(l='foo')
            cmu.Button(l='bar')
            cmu.Button(l='baz')
    wnd.show()

