'use client';

import { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import ProtectedRoute from '@/components/ProtectedRoute';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Search } from 'lucide-react';
import { api } from '@/lib/api-client';

interface ModelAlias {
  model_alias: string;
  actual_model_name: string;
  provider: string;
  input_price_per_million: number;
  output_price_per_million: number;
  access_group_id?: string;
  is_active: boolean;
}

const PROVIDERS = [
  { value: '', label: 'All Providers' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'gemini', label: 'Google Gemini' },
  { value: 'fireworks', label: 'Fireworks AI' },
];

export default function PricingPage() {
  const [models, setModels] = useState<ModelAlias[]>([]);
  const [filteredModels, setFilteredModels] = useState<ModelAlias[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [providerFilter, setProviderFilter] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'input_price' | 'output_price'>('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    loadModels();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [models, searchTerm, providerFilter, sortBy, sortDirection]);

  const loadModels = async () => {
    try {
      setLoading(true);
      const data = await api.getModelAliases();
      setModels(data);
    } catch (error) {
      console.error('Failed to load models:', error);
      setModels([]);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...models];

    // Apply provider filter
    if (providerFilter) {
      filtered = filtered.filter((model) => model.provider === providerFilter);
    }

    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (model) =>
          model.model_alias.toLowerCase().includes(search) ||
          model.actual_model_name.toLowerCase().includes(search) ||
          model.provider.toLowerCase().includes(search)
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = a.model_alias.localeCompare(b.model_alias);
          break;
        case 'input_price':
          comparison = a.input_price_per_million - b.input_price_per_million;
          break;
        case 'output_price':
          comparison = a.output_price_per_million - b.output_price_per_million;
          break;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

    setFilteredModels(filtered);
  };

  const handleSort = (column: 'name' | 'input_price' | 'output_price') => {
    if (sortBy === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDirection('asc');
    }
  };

  const getProviderBadgeColor = (provider: string) => {
    switch (provider) {
      case 'openai':
        return 'bg-green-500';
      case 'anthropic':
        return 'bg-orange-500';
      case 'gemini':
        return 'bg-blue-500';
      case 'fireworks':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getProviderLabel = (provider: string) => {
    const providerObj = PROVIDERS.find(p => p.value === provider);
    return providerObj?.label || provider;
  };

  const formatPrice = (price: number) => {
    return `$${price.toFixed(2)}`;
  };

  const calculateTotalCost = (inputTokens: number, outputTokens: number, model: ModelAlias) => {
    const inputCost = (inputTokens / 1000000) * model.input_price_per_million;
    const outputCost = (outputTokens / 1000000) * model.output_price_per_million;
    return inputCost + outputCost;
  };

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-background">
        <Sidebar />

        <main className="flex-1 overflow-y-auto">
          <div className="p-8">
            <div className="mb-8">
              <h1 className="text-3xl font-bold">Model Pricing</h1>
              <p className="text-muted-foreground">
                View pricing for all available models across providers
              </p>
            </div>

            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Filters</CardTitle>
                <CardDescription>Filter and search available models</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="search">Search Models</Label>
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        id="search"
                        placeholder="Search by model name..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="provider">Provider</Label>
                    <select
                      id="provider"
                      value={providerFilter}
                      onChange={(e) => setProviderFilter(e.target.value)}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    >
                      {PROVIDERS.map((provider) => (
                        <option key={provider.value} value={provider.value}>
                          {provider.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="mt-4 flex items-center gap-4 text-sm text-muted-foreground">
                  <span>
                    Showing {filteredModels.length} of {models.length} models
                  </span>
                  {providerFilter && (
                    <Badge variant="secondary">
                      {getProviderLabel(providerFilter)}
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Model Pricing Overview</CardTitle>
                <CardDescription>
                  All prices shown per 1 million tokens
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center text-muted-foreground py-8">Loading...</div>
                ) : filteredModels.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    No models found matching your filters
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Provider</TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-accent"
                          onClick={() => handleSort('name')}
                        >
                          Model Alias
                          {sortBy === 'name' && (
                            <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                          )}
                        </TableHead>
                        <TableHead>Actual Model</TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-accent text-right"
                          onClick={() => handleSort('input_price')}
                        >
                          Input Price / 1M
                          {sortBy === 'input_price' && (
                            <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                          )}
                        </TableHead>
                        <TableHead
                          className="cursor-pointer hover:bg-accent text-right"
                          onClick={() => handleSort('output_price')}
                        >
                          Output Price / 1M
                          {sortBy === 'output_price' && (
                            <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                          )}
                        </TableHead>
                        <TableHead className="text-right">Example Cost</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredModels.map((model) => {
                        // Example: 10k input, 2k output tokens
                        const exampleCost = calculateTotalCost(10000, 2000, model);

                        return (
                          <TableRow key={model.model_alias}>
                            <TableCell>
                              <Badge
                                className={`${getProviderBadgeColor(model.provider)} text-white`}
                              >
                                {getProviderLabel(model.provider)}
                              </Badge>
                            </TableCell>
                            <TableCell className="font-medium font-mono">
                              {model.model_alias}
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {model.actual_model_name}
                            </TableCell>
                            <TableCell className="text-right font-semibold">
                              {formatPrice(model.input_price_per_million)}
                            </TableCell>
                            <TableCell className="text-right font-semibold">
                              {formatPrice(model.output_price_per_million)}
                            </TableCell>
                            <TableCell className="text-right text-sm text-muted-foreground">
                              {formatPrice(exampleCost)}
                              <div className="text-xs">
                                (10k in, 2k out)
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge
                                className={`${
                                  model.is_active ? 'bg-green-500' : 'bg-gray-500'
                                } text-white`}
                              >
                                {model.is_active ? 'Active' : 'Inactive'}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Pricing Calculator</CardTitle>
                <CardDescription>
                  Estimate costs based on token usage
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="space-y-2">
                    <Label>Input Tokens</Label>
                    <div className="text-2xl font-bold text-muted-foreground">10,000</div>
                  </div>
                  <div className="space-y-2">
                    <Label>Output Tokens</Label>
                    <div className="text-2xl font-bold text-muted-foreground">2,000</div>
                  </div>
                  <div className="space-y-2">
                    <Label>Total Tokens</Label>
                    <div className="text-2xl font-bold text-primary">12,000</div>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">
                  The example cost column shows estimated cost for a typical request with 10,000 input tokens and 2,000 output tokens.
                  Use this to compare relative costs between models.
                </p>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
