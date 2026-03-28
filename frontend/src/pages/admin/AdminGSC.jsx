import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AdminLayout from '../../components/AdminLayout';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { ArrowUp, ArrowDown, Search, Globe, Smartphone, Monitor, Tablet, CheckCircle, XCircle, Clock, AlertTriangle, RefreshCw, Send } from 'lucide-react';
import api from '../../api';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function AdminGSC() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [gscStatus, setGscStatus] = useState({ configured: false });
  const [dashboard, setDashboard] = useState(null);
  const [inspectUrl, setInspectUrl] = useState('');
  const [inspecting, setInspecting] = useState(false);
  const [inspectionResult, setInspectionResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState(null);

  useEffect(() => {
    // Check auth
    const token = localStorage.getItem('adminToken');
    if (!token) {
      navigate('/admin/login');
      return;
    }
    fetchGSCStatus();
    fetchDashboard();
  }, [navigate]);

  const fetchGSCStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/gsc/status`);
      const data = await response.json();
      setGscStatus(data);
    } catch (error) {
      console.error('Failed to fetch GSC status:', error);
    }
  };

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('adminToken');
      const response = await fetch(`${API_URL}/api/gsc/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setDashboard(data);
    } catch (error) {
      console.error('Failed to fetch GSC dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInspectUrl = async () => {
    if (!inspectUrl) return;
    
    setInspecting(true);
    setInspectionResult(null);
    try {
      const token = localStorage.getItem('adminToken');
      const response = await fetch(`${API_URL}/api/gsc/inspect-url?url=${encodeURIComponent(inspectUrl)}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setInspectionResult(data);
    } catch (error) {
      setInspectionResult({ error: error.message });
    } finally {
      setInspecting(false);
    }
  };

  const handleSubmitUrl = async () => {
    if (!inspectUrl) return;
    
    setSubmitting(true);
    setSubmitResult(null);
    try {
      const token = localStorage.getItem('adminToken');
      const response = await fetch(`${API_URL}/api/gsc/submit-url?url=${encodeURIComponent(inspectUrl)}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setSubmitResult(data);
    } catch (error) {
      setSubmitResult({ error: error.message });
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitAllArticles = async () => {
    setSubmitting(true);
    try {
      const token = localStorage.getItem('adminToken');
      const response = await fetch(`${API_URL}/api/gsc/submit-all-articles?limit=50`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setSubmitResult(data);
    } catch (error) {
      setSubmitResult({ error: error.message });
    } finally {
      setSubmitting(false);
    }
  };

  // Not configured state
  if (!gscStatus.configured && !loading) {
    return (
      <AdminLayout title="Google Search Console">
        <div className="space-y-6" data-testid="gsc-not-configured">
        
        <Card className="border-yellow-500/50 bg-yellow-500/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-600">
              <AlertTriangle className="w-5 h-5" />
              Nicht konfiguriert
            </CardTitle>
            <CardDescription>
              Google Search Console ist noch nicht eingerichtet. Folge diesen Schritten:
            </CardDescription>
          </CardHeader>
          <CardContent>
            {dashboard?.setup_instructions && (
              <ol className="list-decimal list-inside space-y-2 text-sm">
                {Object.entries(dashboard.setup_instructions).map(([step, instruction]) => (
                  <li key={step} className="text-gray-700">{instruction}</li>
                ))}
              </ol>
            )}
            
            <div className="mt-6 p-4 bg-gray-100 rounded-lg">
              <h4 className="font-semibold mb-2">Service Account E-Mail</h4>
              <p className="text-sm text-gray-600 mb-4">
                Füge diese E-Mail als Nutzer (mit vollem Zugriff) in der Google Search Console hinzu:
              </p>
              <code className="text-xs bg-white px-2 py-1 rounded border">
                your-service-account@your-project.iam.gserviceaccount.com
              </code>
            </div>
          </CardContent>
        </Card>
      </div>
      </AdminLayout>
    );
  }

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toLocaleString('de-DE') || '0';
  };

  const getDeviceIcon = (device) => {
    switch(device?.toLowerCase()) {
      case 'mobile': return <Smartphone className="w-4 h-4" />;
      case 'tablet': return <Tablet className="w-4 h-4" />;
      default: return <Monitor className="w-4 h-4" />;
    }
  };

  return (
    <AdminLayout title="Google Search Console">
    <div className="space-y-6" data-testid="gsc-dashboard">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <p className="text-sm text-gray-500">{gscStatus.site_url}</p>
        </div>
        <Button onClick={fetchDashboard} variant="outline" size="sm">
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Aktualisieren
        </Button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      ) : dashboard?.error ? (
        <Card className="border-red-500/50">
          <CardContent className="pt-6">
            <p className="text-red-600">{dashboard.error}</p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card data-testid="gsc-clicks-card">
              <CardHeader className="pb-2">
                <CardDescription>Klicks (7 Tage)</CardDescription>
                <CardTitle className="text-3xl">
                  {formatNumber(dashboard?.overview?.clicks_7d)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`flex items-center text-sm ${dashboard?.overview?.clicks_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {dashboard?.overview?.clicks_change >= 0 ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
                  <span>{Math.abs(dashboard?.overview?.clicks_change || 0)}% vs. Vorwoche</span>
                </div>
              </CardContent>
            </Card>

            <Card data-testid="gsc-impressions-card">
              <CardHeader className="pb-2">
                <CardDescription>Impressionen (7 Tage)</CardDescription>
                <CardTitle className="text-3xl">
                  {formatNumber(dashboard?.overview?.impressions_7d)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`flex items-center text-sm ${dashboard?.overview?.impressions_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {dashboard?.overview?.impressions_change >= 0 ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
                  <span>{Math.abs(dashboard?.overview?.impressions_change || 0)}% vs. Vorwoche</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Durchschn. CTR</CardDescription>
                <CardTitle className="text-3xl">
                  {dashboard?.overview?.ctr_7d || 0}%
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-500">Klickrate der letzten 7 Tage</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>Durchschn. Position</CardDescription>
                <CardTitle className="text-3xl">
                  {dashboard?.overview?.position_7d || 0}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-500">In Google Suchergebnissen</p>
              </CardContent>
            </Card>
          </div>

          {/* URL Inspection & Submission */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="w-5 h-5" />
                URL-Prüfung & Indexierung
              </CardTitle>
              <CardDescription>
                Prüfe den Indexierungsstatus einer URL oder reiche sie zur Indexierung ein
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="https://transfernews.de/news/artikel-slug"
                  value={inspectUrl}
                  onChange={(e) => setInspectUrl(e.target.value)}
                  className="flex-1"
                  data-testid="gsc-url-input"
                />
                <Button onClick={handleInspectUrl} disabled={inspecting || !inspectUrl}>
                  {inspecting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  <span className="ml-2">Prüfen</span>
                </Button>
                <Button onClick={handleSubmitUrl} disabled={submitting || !inspectUrl} variant="outline">
                  {submitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  <span className="ml-2">Einreichen</span>
                </Button>
              </div>

              {/* Inspection Result */}
              {inspectionResult && (
                <div className={`p-4 rounded-lg ${inspectionResult.error ? 'bg-red-50 border border-red-200' : inspectionResult.indexed ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'}`}>
                  {inspectionResult.error ? (
                    <div className="flex items-center gap-2 text-red-700">
                      <XCircle className="w-5 h-5" />
                      <span>Fehler: {inspectionResult.error}</span>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        {inspectionResult.indexed ? (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        ) : (
                          <Clock className="w-5 h-5 text-yellow-600" />
                        )}
                        <span className="font-semibold">
                          {inspectionResult.indexed ? 'Indexiert' : 'Nicht indexiert'}
                        </span>
                        <span className="text-sm text-gray-500">— {inspectionResult.coverage_state}</span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm mt-3">
                        <div>
                          <span className="text-gray-500">Zuletzt gecrawlt:</span>
                          <span className="ml-2">{inspectionResult.last_crawl_time ? new Date(inspectionResult.last_crawl_time).toLocaleString('de-DE') : 'Nie'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Crawled als:</span>
                          <span className="ml-2">{inspectionResult.crawled_as}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Mobile Usability:</span>
                          <span className={`ml-2 ${inspectionResult.mobile_usability?.verdict === 'PASS' ? 'text-green-600' : 'text-yellow-600'}`}>
                            {inspectionResult.mobile_usability?.verdict}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">robots.txt:</span>
                          <span className="ml-2">{inspectionResult.robots_txt_state}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Submit Result */}
              {submitResult && (
                <div className={`p-4 rounded-lg ${submitResult.error ? 'bg-red-50 border border-red-200' : 'bg-blue-50 border border-blue-200'}`}>
                  {submitResult.error ? (
                    <div className="flex items-center gap-2 text-red-700">
                      <XCircle className="w-5 h-5" />
                      <span>Fehler: {submitResult.error}</span>
                    </div>
                  ) : submitResult.submitted !== undefined ? (
                    <div className="flex items-center gap-2 text-blue-700">
                      <CheckCircle className="w-5 h-5" />
                      <span>{submitResult.submitted} URLs zur Indexierung eingereicht</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-blue-700">
                      <CheckCircle className="w-5 h-5" />
                      <span>URL zur Indexierung eingereicht</span>
                    </div>
                  )}
                </div>
              )}

              {/* Bulk Submit */}
              <div className="pt-4 border-t">
                <Button onClick={handleSubmitAllArticles} disabled={submitting} variant="secondary" className="w-full">
                  {submitting ? <RefreshCw className="w-4 h-4 animate-spin mr-2" /> : <Globe className="w-4 h-4 mr-2" />}
                  Alle Artikel zur Indexierung einreichen (max. 50)
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Top Queries & Pages */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Queries */}
            <Card>
              <CardHeader>
                <CardTitle>Top Suchanfragen</CardTitle>
                <CardDescription>Meistgeklickte Suchbegriffe (7 Tage)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {dashboard?.top_queries?.slice(0, 10).map((row, idx) => (
                    <div key={idx} className="flex items-center justify-between py-2 border-b last:border-0">
                      <div className="flex-1">
                        <span className="text-sm font-medium">{row.keys?.[0]}</span>
                      </div>
                      <div className="flex gap-4 text-sm text-gray-500">
                        <span title="Klicks">{row.clicks} Klicks</span>
                        <span title="Impressionen">{formatNumber(row.impressions)} Imp.</span>
                        <span title="Position">Pos. {row.position}</span>
                      </div>
                    </div>
                  ))}
                  {(!dashboard?.top_queries || dashboard.top_queries.length === 0) && (
                    <p className="text-sm text-gray-500 text-center py-4">Keine Daten verfügbar</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Top Pages */}
            <Card>
              <CardHeader>
                <CardTitle>Top Seiten</CardTitle>
                <CardDescription>Meistgeklickte Seiten (7 Tage)</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {dashboard?.top_pages?.slice(0, 10).map((row, idx) => {
                    const url = row.keys?.[0] || '';
                    const path = url.replace(gscStatus.site_url, '');
                    return (
                      <div key={idx} className="flex items-center justify-between py-2 border-b last:border-0">
                        <div className="flex-1 truncate pr-4">
                          <span className="text-sm font-medium" title={url}>{path || '/'}</span>
                        </div>
                        <div className="flex gap-4 text-sm text-gray-500 whitespace-nowrap">
                          <span>{row.clicks} Klicks</span>
                          <span>{row.ctr}% CTR</span>
                        </div>
                      </div>
                    );
                  })}
                  {(!dashboard?.top_pages || dashboard.top_pages.length === 0) && (
                    <p className="text-sm text-gray-500 text-center py-4">Keine Daten verfügbar</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Device & Country Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Device Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Geräte</CardTitle>
                <CardDescription>Performance nach Gerätetyp</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {dashboard?.device_breakdown?.map((row, idx) => {
                    const device = row.keys?.[0];
                    const totalClicks = dashboard.device_breakdown.reduce((sum, r) => sum + r.clicks, 0);
                    const percentage = totalClicks > 0 ? (row.clicks / totalClicks * 100).toFixed(1) : 0;
                    
                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {getDeviceIcon(device)}
                            <span className="capitalize">{device}</span>
                          </div>
                          <span className="text-sm text-gray-500">{row.clicks} Klicks ({percentage}%)</span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-2">
                          <div 
                            className="bg-[#79B92A] h-2 rounded-full" 
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Country Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Länder</CardTitle>
                <CardDescription>Top Länder nach Klicks</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {dashboard?.country_breakdown?.map((row, idx) => {
                    const country = row.keys?.[0];
                    const countryNames = {
                      'deu': 'Deutschland',
                      'aut': 'Österreich',
                      'che': 'Schweiz',
                      'usa': 'USA',
                      'gbr': 'Großbritannien',
                      'fra': 'Frankreich',
                      'esp': 'Spanien',
                      'ita': 'Italien'
                    };
                    
                    return (
                      <div key={idx} className="flex items-center justify-between py-2 border-b last:border-0">
                        <span>{countryNames[country?.toLowerCase()] || country}</span>
                        <div className="flex gap-4 text-sm text-gray-500">
                          <span>{row.clicks} Klicks</span>
                          <span>{formatNumber(row.impressions)} Imp.</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
    </AdminLayout>
  );
}
