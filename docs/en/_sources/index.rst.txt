=========================================
  cymel for Maya (Preview Version)
=========================================

Maya のスクリプティングを Python らしく簡潔で直感的なものとするためのオープンソースの Python モジュールです。
pymel__ に多大な影響を受けて開発されましたが、本家より軽量で軽快なプログラミングを可能とします。

__ https://github.com/LumaPictures/pymel

cymel の C は C++ の C です。コアは C++ で実装し、高速に動作させることを狙っています。
現在はフル Python で書かれたプレビュー版ですが、現段階でも非常に軽量です。

正式版のコアは C++ 実装に置き換わる予定ですが、その後も Python 版は維持され、常時切替可能にする計画です。
Maya バージョンアップ時に大きな変更があった場合など、C++ 実装では労力がかかる対応も Python 版は早期に作業を終えられるようにするとともに、
全てのプラットフォームでバイナリをビルドできなくとも最低限の動作を保証します。


Contents
=====================================
.. toctree::
    :maxdepth: 2

    installation
    whycymel
    gettingstarted
    modules


Indices and tables
=====================================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
