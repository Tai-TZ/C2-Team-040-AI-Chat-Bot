export type SubLocation = {
  code: string;
  name: string;
  tag: string;
};

export type Destination = {
  destination_code: string;
  destination_name: string;
  sub_locations: SubLocation[];
};

export type DestinationsResponse = {
  destinations: Destination[];
};

export type TicketPrice = {
  name: string;
  salePrice: number;
  originalPrice?: number | null;
  guestType?: string;
  isDefault?: boolean;
  error?: string;
};

export type PricesResponse = {
  supplierCode: string;
  usingDate: string;
  siteName?: string | null;
  ticketCount: number;
  tickets: TicketPrice[];
};
