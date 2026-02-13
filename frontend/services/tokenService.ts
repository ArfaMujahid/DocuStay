
export interface USATToken {
  tokenId: string;
  issuedAt: string;
  expiresAt: string;
  guestName: string;
  propertyAddress: string;
  status: 'ACTIVE' | 'EXPIRED' | 'REVOKED';
  signature: string;
}

export const generateUSATToken = (data: any): USATToken => {
  const tokenId = `USAT-${new Date().getFullYear()}-${Math.random().toString(36).substring(2, 10).toUpperCase()}`;
  
  // In a real app, this would be a real cryptographic signature of the payload
  const signature = btoa(JSON.stringify({ id: tokenId, exp: data.checkoutDate, salt: Math.random() }));

  return {
    tokenId,
    issuedAt: new Date().toISOString(),
    expiresAt: data.checkoutDate,
    guestName: data.guestName,
    propertyAddress: data.propertyAddress,
    status: 'ACTIVE',
    signature
  };
};
