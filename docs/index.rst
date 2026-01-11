B2B Complaint Analyzer Documentation
=====================================

Welcome to the B2B Complaint Analyzer documentation.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   user_guide
   developer_guide
   api
   api_reference

Overview
--------

The B2B Complaint Analyzer is a Streamlit web application that extracts unmet needs from 1-2 star reviews of popular B2B SaaS tools, identifies high-demand patterns, and uses xAI's Grok to generate actionable product ideas with 4-week roadmaps.

Features
--------

* Automated Review Scraping: Scrapes 1-2 star reviews from G2.com and Capterra
* Pattern Detection: Identifies complaint patterns using keyword matching and ML clustering
* AI-Powered Analysis: Uses xAI Grok to analyze patterns and generate product ideas
* Actionable Roadmaps: Creates detailed 4-week solo founder roadmaps

Quick Start
-----------

.. code-block:: bash

   pip install -r requirements.txt
   streamlit run app_v2.py

For more information, see the :doc:`user_guide` or :doc:`developer_guide`.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
