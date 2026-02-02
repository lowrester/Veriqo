import React, { useState } from 'react';
import { Save, Upload } from 'lucide-react';

export const BrandingPage: React.FC = () => {
    const [brandName, setBrandName] = useState('Veriqo');
    const [primaryColor, setPrimaryColor] = useState('#2563eb');

    const handleSave = (e: React.FormEvent) => {
        e.preventDefault();
        // Save logic would go here
        alert('Branding settings saved!');
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold tracking-tight">Branding Settings</h1>
                <p className="text-muted-foreground">
                    Customize the look and feel of your Veriqo instance.
                </p>
            </div>

            <div className="rounded-lg border bg-card p-6">
                <form onSubmit={handleSave} className="space-y-8">

                    {/* Brand Name */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium">Brand Name</label>
                        <input
                            type="text"
                            value={brandName}
                            onChange={(e) => setBrandName(e.target.value)}
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        />
                        <p className="text-xs text-muted-foreground">
                            This name will appear in the page title and navigation.
                        </p>
                    </div>

                    {/* Logo Upload */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium">Logo</label>
                        <div className="flex items-center gap-4">
                            <div className="flex h-20 w-20 items-center justify-center rounded-lg border border-dashed">
                                <Upload className="h-6 w-6 text-muted-foreground" />
                            </div>
                            <button
                                type="button"
                                className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
                            >
                                Upload New Logo
                            </button>
                        </div>
                    </div>

                    {/* Primary Color */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium">Primary Color</label>
                        <div className="flex gap-2">
                            <input
                                type="color"
                                value={primaryColor}
                                onChange={(e) => setPrimaryColor(e.target.value)}
                                className="h-10 w-20 cursor-pointer rounded-md border p-1"
                            />
                            <input
                                type="text"
                                value={primaryColor}
                                onChange={(e) => setPrimaryColor(e.target.value)}
                                className="flex h-10 w-32 rounded-md border border-input bg-background px-3 py-2 text-sm"
                            />
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Used for buttons, links, and active states.
                        </p>
                    </div>

                    <div className="pt-4">
                        <button
                            type="submit"
                            className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
                        >
                            <Save className="mr-2 h-4 w-4" />
                            Save Changes
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
