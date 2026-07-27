<?xml version="1.0" encoding="UTF-8"?>
<!-- XSLT transformation from TEI/XML to annotated HTML output -->

<xsl:stylesheet version="1.0"
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:tei="http://www.tei-c.org/ns/1.0">

   <xsl:output method="html" encoding="UTF-8" indent="yes"/>

   <xsl:template match="/">
      <html lang="en">
         <head>
            <meta charset="UTF-8"/>
            <title>
               <xsl:value-of select="//tei:titleStmt/tei:title"/>
               <xsl:text> - TEI Edition</xsl:text>
            </title>

            <style>
               body {
                  font-family: Georgia, serif;
                  max-width: 900px;
                  margin: 40px auto;
                  padding: 0 22px;
                  line-height: 1.75;
                  color: #1d1d1d;
                  background: #faf9f6;
               }

               h1 {
                  font-size: 2.1em;
                  border-bottom: 2px solid #9c6b30;
                  padding-bottom: 10px;
                  margin-bottom: 0.2em;
               }

               .subtitle {
                  color: #6e5a45;
                  font-style: italic;
                  margin-bottom: 2em;
               }

               .legend {
                  background: #fff;
                  border: 1px solid #ddd2c2;
                  padding: 15px 20px;
                  margin: 28px 0;
                  border-radius: 6px;
                  font-size: 0.92em;
               }

               .legend span {
                  display: inline-block;
                  margin-right: 16px;
                  margin-bottom: 6px;
               }

               .persName {
                  color: #8b0000;
                  font-weight: bold;
                  border-bottom: 1px dotted #8b0000;
               }

               .placeName {
                  color: #004b7a;
                  font-weight: bold;
                  border-bottom: 1px dotted #004b7a;
               }

               .orgName {
                  color: #5a3e91;
                  font-weight: bold;
                  border-bottom: 1px dotted #5a3e91;
               }

               .event {
                  color: #2e6b2e;
                  font-style: italic;
                  border-bottom: 1px dotted #2e6b2e;
               }

               .term {
                  color: #7a4000;
                  font-weight: bold;
                  border-bottom: 1px dotted #7a4000;
               }

               .documentary,
               .digitalResource {
                  color: #555;
                  font-style: italic;
                  border-bottom: 1px dotted #555;
               }

               .date {
                  color: #6b4b00;
               }

               .quote {
                  color: #333;
                  background: #f1eadf;
                  padding: 0 3px;
               }

               .source {
                  font-size: 0.85em;
                  color: #777;
                  margin-top: 40px;
                  border-top: 1px solid #ddd2c2;
                  padding-top: 12px;
               }
            </style>
         </head>

         <body>
            <h1>
               <xsl:value-of select="//tei:titleStmt/tei:title"/>
            </h1>

            <div class="subtitle">
               <xsl:value-of select="//tei:titleStmt/tei:subtitle"/>
            </div>

            <div class="legend">
               <strong>Annotation Legend:</strong>
               <br/>
               <span class="persName">Person</span>
               <span class="placeName">Place / Museum</span>
               <span class="orgName">Organisation</span>
               <span class="event">Event</span>
               <span class="term">Concept</span>
               <span class="documentary">Documentary</span>
               <span class="digitalResource">Digital resource</span>
               <span class="date">Date</span>
               <q class="quote">Quotation</q>
            </div>

            <xsl:apply-templates select="//tei:text/tei:body//tei:p"/>

            <div class="source">
               <p>Source: Wikipedia pages “Gare d’Orsay” and “Musée d’Orsay”.</p>
               <p>TEI encoding and XML to HTML transformation: Ekaterina Petukhova - University of Bologna.</p>
            </div>
         </body>
      </html>
   </xsl:template>

   <!-- Paragraphs -->
   <xsl:template match="tei:p">
      <p>
         <xsl:apply-templates/>
      </p>
   </xsl:template>

   <!-- People -->
   <xsl:template match="tei:persName">
      <span class="persName">
         <xsl:attribute name="title">
            <xsl:text>Person</xsl:text>
            <xsl:if test="@ref">
               <xsl:text>: </xsl:text>
               <xsl:value-of select="@ref"/>
            </xsl:if>
         </xsl:attribute>
         <xsl:apply-templates/>
      </span>
   </xsl:template>

   <!-- Places / buildings / museums -->
   <xsl:template match="tei:placeName">
      <span class="placeName">
         <xsl:attribute name="title">
            <xsl:text>Place or museum</xsl:text>
            <xsl:if test="@ref">
               <xsl:text>: </xsl:text>
               <xsl:value-of select="@ref"/>
            </xsl:if>
         </xsl:attribute>
         <xsl:apply-templates/>
      </span>
   </xsl:template>

   <!-- Organisations -->
   <xsl:template match="tei:orgName">
      <span class="orgName">
         <xsl:attribute name="title">
            <xsl:text>Organisation</xsl:text>
            <xsl:if test="@ref">
               <xsl:text>: </xsl:text>
               <xsl:value-of select="@ref"/>
            </xsl:if>
         </xsl:attribute>
         <xsl:apply-templates/>
      </span>
   </xsl:template>

   <!-- Events encoded with rs type event -->
   <xsl:template match="tei:rs[@type='event']">
      <span class="event">
         <xsl:attribute name="title">
            <xsl:text>Event</xsl:text>
            <xsl:if test="@ref">
               <xsl:text>: </xsl:text>
               <xsl:value-of select="@ref"/>
            </xsl:if>
         </xsl:attribute>
         <xsl:apply-templates/>
      </span>
   </xsl:template>

   <!-- Documentary / media entity -->
   <xsl:template match="tei:rs[@type='documentary']">
      <span class="documentary">
         <xsl:attribute name="title">
            <xsl:text>Documentary</xsl:text>
            <xsl:if test="@ref">
               <xsl:text>: </xsl:text>
               <xsl:value-of select="@ref"/>
            </xsl:if>
         </xsl:attribute>
         <xsl:apply-templates/>
      </span>
   </xsl:template>

   <!-- Digital resource entity -->
   <xsl:template match="tei:rs[@type='digitalResource']">
      <span class="digitalResource">
         <xsl:attribute name="title">
            <xsl:text>Digital resource</xsl:text>
            <xsl:if test="@ref">
               <xsl:text>: </xsl:text>
               <xsl:value-of select="@ref"/>
            </xsl:if>
         </xsl:attribute>
         <xsl:apply-templates/>
      </span>
   </xsl:template>

   <!-- Concepts -->
   <xsl:template match="tei:term">
      <span class="term">
         <xsl:attribute name="title">
            <xsl:text>Concept</xsl:text>
            <xsl:if test="@ref">
               <xsl:text>: </xsl:text>
               <xsl:value-of select="@ref"/>
            </xsl:if>
         </xsl:attribute>
         <xsl:apply-templates/>
      </span>
   </xsl:template>

   <!-- Dates -->
   <xsl:template match="tei:date">
      <span class="date">
         <xsl:attribute name="title">
            <xsl:choose>
               <xsl:when test="@when">
                  <xsl:value-of select="@when"/>
               </xsl:when>
               <xsl:when test="@from or @to">
                  <xsl:value-of select="@from"/>
                  <xsl:text> - </xsl:text>
                  <xsl:value-of select="@to"/>
               </xsl:when>
               <xsl:otherwise>Date</xsl:otherwise>
            </xsl:choose>
         </xsl:attribute>
         <xsl:apply-templates/>
      </span>
   </xsl:template>

   <!-- Quotations / textual phenomena -->
   <xsl:template match="tei:quote">
      <q class="quote">
         <xsl:apply-templates/>
      </q>
   </xsl:template>

   <!-- Titles inside text -->
   <xsl:template match="tei:title">
      <em>
         <xsl:apply-templates/>
      </em>
   </xsl:template>

   <!-- Default: copy text content -->
   <xsl:template match="text()">
      <xsl:value-of select="."/>
   </xsl:template>

</xsl:stylesheet>
