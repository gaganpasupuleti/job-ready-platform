/** Registration is offered only when the API explicitly says it is open. */
export function canOfferRegistration(enabled: boolean | null | undefined): boolean {
  return enabled === true
}
