<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tei="http://www.tei-c.org/ns/1.0" exclude-result-prefixes="tei">
<xsl:output method="html" encoding="UTF-8" indent="yes"/>
<xsl:template match="/"><html lang="en"><head><meta charset="UTF-8"/><title>Musée d’Orsay — TEI Edition (XSLT)</title></head><body><h1>Musée d’Orsay TEI Edition</h1><xsl:apply-templates select="//tei:text/tei:body"/></body></html></xsl:template>
<xsl:template match="tei:p"><p><xsl:apply-templates/></p></xsl:template>
<xsl:template match="tei:div"><section><xsl:apply-templates/></section></xsl:template>
<xsl:template match="tei:head"><h2><xsl:apply-templates/></h2></xsl:template>
<xsl:template match="tei:title"><em><xsl:apply-templates/></em></xsl:template>
<xsl:template match="tei:*[@ref]"><mark><xsl:attribute name="title"><xsl:value-of select="@ref"/></xsl:attribute><xsl:apply-templates/></mark></xsl:template>
<xsl:template match="tei:date"><time><xsl:apply-templates/></time></xsl:template>
<xsl:template match="text()"><xsl:value-of select="."/></xsl:template>
</xsl:stylesheet>